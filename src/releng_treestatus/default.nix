{ releng_pkgs
}:

let

  inherit (releng_pkgs.lib) mkBackend filterSource mysql2sqlite mysql2postgresql;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  beforeSQL = ''
    drop table if exists treestatus_change_trees;
    drop table if exists treestatus_changes;
    drop table if exists treestatus_log;
    drop table if exists treestatus_trees;
  '';

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  releng_common = import ./../../lib/releng_common {
    inherit releng_pkgs python;
    extras = ["api" "auth" "cors" "log" "db" "cache"];
  };

  self = mkBackend rec {
    inherit python releng_common;
    name = "releng_treestatus";
    version = fileContents ./../../VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      [ python.packages."flake8"
        python.packages."pytest"
        python.packages."ipdb"
      ];
    propagatedBuildInputs =
      [ python.packages."pytz"
        python.packages."SQLAlchemy"
        python.packages."Flask"
        python.packages."Flask-Login"
        python.packages."Werkzeug"
      ];
    passthru = {
      mysql2sqlite = mysql2sqlite {
        inherit name beforeSQL;
        afterSQL = ''
          drop table if exists archiver_tasks;
          drop table if exists auth_tokens;
          drop table if exists badpenny_jobs;
          drop table if exists badpenny_job_logs;
          drop table if exists badpenny_tasks;
          drop table if exists celery_taskmeta;
          drop table if exists celery_tasksetmeta;
          drop table if exists oauth2_clients;
          drop table if exists oauth2_grants;
          drop table if exists oauth2_tokens;
          drop table if exists relengapi_version;
          drop table if exists slaveloan_history;
          drop table if exists slaveloan_humans;
          drop table if exists slaveloan_loans;
          drop table if exists slaveloan_machines;
          drop table if exists slaveloan_manualactions;
          drop table if exists tooltool_batch_files;
          drop table if exists tooltool_batches;
          drop table if exists tooltool_file_instances;
          drop table if exists tooltool_files;
          drop table if exists tooltool_pending_upload;
        '';
      };
      mysql2postgresql = mysql2postgresql {
        inherit name beforeSQL;
        config = ''
          only_tables:
           - treestatus_change_trees
           - treestatus_changes
           - treestatus_log
           - treestatus_trees
        '';
      };
      update = writeScript "update-${name}" ''
        pushd src/${name}
        ${pypi2nix}/bin/pypi2nix -v \
         -V 3.5 \
         -E "postgresql" \
         -r ../../lib/releng_common/requirements-dev.txt \
         -r requirements.txt \
         -r requirements-dev.txt \
         -r requirements-nix.txt
        popd
      '';
    };
  };

in self
