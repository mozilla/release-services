{ releng_pkgs
}: 

let

  inherit (releng_pkgs.lib) mkBackend mkTaskclusterHook;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) removeSuffix;
  inherit (releng_pkgs.tools) pypi2nix;

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

  # TODO: move this migrate scripts to releng_pkgs.tools
  migrate = import ./migrate.nix { inherit releng_pkgs; };

  self = mkBackend rec {
    name = "releng_clobberer";
    version = removeSuffix "\n" (builtins.readFile ./../../VERSION);
    python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
    src = ./.;
    srcs = [
      "./../../lib/releng_common"
      "./../${name}"
    ];
    buildRequirements =
      [ ./requirements-dev.txt
        ./requirements-setup.txt
      ];
    propagatedRequirements =
      [ ./../../lib/releng_common/requirements.txt
        ./requirements.txt
        ./requirements-prod.txt
      ];
    passthru = {
      mysql2sqlite = migrate.mysql2sqlite { inherit name beforeSQL afterSQL; };
      mysql2postgresql = migrate.mysql2postgresql { inherit name beforeSQL afterSQL; };
      taskclusterHooks = {
        master = {
          taskcluster_cache = mkTaskclusterHook {
            name = "create taskcluster cache";
            owner = "rgarbas@mozilla.com";
            schedule = [ "*/15 * * * * *" ];
            taskImage = self.docker;
            taskCommand = [ "flask" "taskcluster_workertypes" ">" "/taskcluster_cache.json" ];
          };
        };
        #update = mkTaskclusterHook {
        #  name = "Updating sources";
        #  owner = "rgarbas@mozilla.com";
        #  schedule = [];
        #  taskImage = self.docker;
        #  taskCommand = [ "echo" "'Hello World!'" ];
        #};
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
