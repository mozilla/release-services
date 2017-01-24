{ releng_pkgs
}: 

let

  inherit (releng_pkgs.lib) mkBackend mkTaskclusterHook filterSource;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  releng_common = import ./../../lib/releng_common {
    inherit releng_pkgs python;
    extras = ["api" "auth" "cors" "log" "db" ];
  };

  mkBot = branch :
    let
      cacheKey = "shipit-bot-" + branch;
      secretsKey = "project/shipit/bot/" + branch;
    in
      mkTaskclusterHook {
        name = "Shipit bot updating bug analysis";
        owner = "babadie@mozilla.com";
        schedule = [ "0 */30 * * * *" ];  # every 30 min
        taskImage = self.docker;
        scopes = [
          # Used by taskclusterProxy
          ("secrets:get:" + secretsKey)

          # Used by cache
          ("docker-worker:cache:" + cacheKey)
        ];
        cache = {
          "${cacheKey}" = "/cache";
        };
        taskEnv = {
          "SSL_CERT_FILE" = "${releng_pkgs.pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
        };
        taskCommand = [
          "/bin/shipit-dashboard-bot"
          "--secrets"
          secretsKey
          "--cache-root"
          "/cache"
        ];
      };

  self = mkBackend rec {
    inherit python releng_common;
    production = true;
    name = "shipit_dashboard";
    version = fileContents ./../../VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      [ python.packages."flake8"
        python.packages."pytest"
        python.packages."ipdb"
        python.packages."responses"
      ];
    propagatedBuildInputs =
      [ 
        python.packages."libmozdata"
        python.packages."python-hglib"
        python.packages.certifi
				releng_pkgs.pkgs.mercurial
      ];
    passthru = {
      taskclusterHooks = {
        master = {
        };
        staging = {
          bot = mkBot "staging";
        };
        production = {
          bot = mkBot "production";
        };
      };
      update = writeScript "update-${name}" ''
        pushd src/${name}
        ${pypi2nix}/bin/pypi2nix -v \
         -V 3.5 \
         -E "postgresql libffi openssl pkgconfig freetype.dev" \
         -r ../../lib/releng_common/requirements-dev.txt \
         -r requirements.txt \
         -r requirements-dev.txt \
         -r requirements-nix.txt
        popd
      '';
    };
  };

in self
