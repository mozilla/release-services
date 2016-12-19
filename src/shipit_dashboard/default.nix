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

# Update the database with bugs analysis
# CACHE_TYPE=filesystem \
# CACHE_DIR=$PWD/src/shipit_dashboard/cache \
# DATABASE_URL=engine://XXXXX \
# FLASK_APP=shipit_dashboard \
# APP_SETTINGS=$PWD/src/shipit_dashboard/settings.py \
#   nix-shell nix/default.nix -A shipit_dashboard \
#    --run "flask run_workflow_local"
