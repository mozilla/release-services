{ releng_pkgs 
}: 

let

  inherit (releng_pkgs.lib) mkTaskclusterHook mkPython fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript makeWrapper fetchurl;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) fileContents optional licenses;
  inherit (releng_pkgs.tools) pypi2nix mercurial;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  name = "mozilla-shipit-bot-uplift";
  dirname = "shipit_bot_uplift";

  mkBot = branch:
    let
      cacheKey = "shipit-bot-" + branch;
      secretsKey = "repo:github.com/mozilla-releng/services:branch:" + branch;
    in
      mkTaskclusterHook {
        name = "Shipit bot updating bug analysis";
        owner = "babadie@mozilla.com";
        schedule = [ "0 0 * * * *" ];  # every hour
        taskImage = self.docker;
        scopes = [
          # Used by taskclusterProxy
          ("secrets:get:" + secretsKey)

          # Email notifications
          "notify:email:babadie@mozilla.com"
          "notify:email:sledru@mozilla.com"

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
          "/bin/shipit-bot-uplift"
          "--secrets"
          secretsKey
          "--cache-root"
          "/cache"
        ];
      };

  self = mkPython {
    inherit python name dirname;
    inProduction = true;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      fromRequirementsFile ./requirements-dev.txt python.packages;
    propagatedBuildInputs =
      fromRequirementsFile ./requirements.txt python.packages;
    postInstall = ''
      mkdir -p $out/bin
      ln -s ${mercurial}/bin/hg $out/bin
    '';
		shellHook = ''
			export PATH="${mercurial}/bin:$PATH"
		'';
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
        pushd ${self.src_path}
        ${pypi2nix}/bin/pypi2nix -v \
          -V 3.5 \
          -E "libffi openssl pkgconfig freetype.dev" \
          -r requirements.txt \
          -r requirements-dev.txt
        popd
      '';
    };
  };

in self
