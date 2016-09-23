{ releng_pkgs
}: 

let

  inherit (releng_pkgs.lib) mkBackend mkTaskclusterHook;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) removeSuffix;
  inherit (releng_pkgs.tools) pypi2nix;

  self = mkBackend rec {
    name = "shipit_dashboard";
    version = removeSuffix "\n" (builtins.readFile ./../../VERSION);
    python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
    src = ./.;
    srcs = [
      "./../releng_common"
      "./../${name}"
    ];
    buildRequirements =
      [ ./requirements-dev.txt
        ./requirements-setup.txt
      ];
    propagatedRequirements =
      [ ./../releng_common/requirements.txt
        ./requirements.txt
        ./requirements-prod.txt
      ];
    passthru = {
      taskclusterHooks = {
        taskcluster_analysis = mkTaskclusterHook {
          name = "update bugzilla analysis";
          owner = "bastien@nextcairn.com";
          schedule = [ "0 */2 * * * *" ];
          taskImage = self.docker;
          taskCommand = [ "flask" "run_workflow_local" ];
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

# Update the database with bugs analysis
# CACHE_TYPE=filesystem \
# CACHE_DIR=$PWD/src/shipit_dashboard/cache \
# DATABASE_URL=engine://XXXXX \
# FLASK_APP=shipit_dashboard \
# APP_SETTINGS=$PWD/src/shipit_dashboard/settings.py \
#   nix-shell nix/default.nix -A shipit_dashboard \
#    --run "flask run_workflow_local"
