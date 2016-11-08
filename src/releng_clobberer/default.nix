{ releng_pkgs
}: 

let

  inherit (releng_pkgs.lib) mkBackend mkTaskclusterHook filterSource mysql2sqlite mysql2postgresql;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  releng_common = import ./../../lib/releng_common {
    inherit releng_pkgs python;
    extras = ["api" "auth" "cors" "log" "db"];
  };

  beforeSQL = ''
    DROP TABLE IF EXISTS clobberer_builds;
    DROP TABLE IF EXISTS clobberer_times;
    DROP TABLE IF EXISTS builds;
    DROP TABLE IF EXISTS clobber_times;
  '';
  afterSQL = ''
    ALTER TABLE builds        RENAME TO clobberer_builds;
    ALTER TABLE clobber_times RENAME TO clobberer_times;
  '';

  taskcluster_cache = mkTaskclusterHook {
    name = "create taskcluster cache";
    owner = "rgarbas@mozilla.com";
    schedule = [ "0 */20 * * * *" ];  # every 20 min
    taskImage = self.docker;
    taskEnv = {
      DATABASE_URL = "sqlite://";
    };
    taskCommand = [
      "/bin/sh"
      "-c"
      "/bin/flask taskcluster_cache > /taskcluster_cache.json"
    ];
    taskArtifacts = {
      "taskcluster_cache.json" = {
        type = "file";
        path = "/taskcluster_cache.json";
      };
    };
  };

  self = mkBackend rec {
    inherit python;
    name = "releng_clobberer";
    version = fileContents ./../../VERSION;
    src = filterSource ./. { inherit name; };
    propagatedBuildInputs =
      [ releng_common
      ];
    passthru = {
      mysql2sqlite = mysql2sqlite { inherit name beforeSQL afterSQL; };
      mysql2postgresql = mysql2postgresql { inherit name beforeSQL afterSQL; };
      taskclusterHooks = {
        master = {
        };
        staging = {
          inherit taskcluster_cache;
        };
        production = {
          inherit taskcluster_cache;
        };
      };
      update = writeScript "update-${name}" ''
        pushd src/${name}
        ${pypi2nix}/bin/pypi2nix -v \
         -V 3.5 \
         -E "postgresql libffi openssl" \
         -r requirements.txt \
         -r requirements-setup.txt \
         -r requirements-dev.txt \
         -r requirements-prod.txt 
        popd
      '';
    };
  };

in self
