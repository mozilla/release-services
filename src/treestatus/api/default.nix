{ releng_pkgs
}:

let

  inherit (releng_pkgs.lib) mkBackend2 fromRequirementsFile filterSource mysql2postgresql;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  beforeSQL = ''
    drop table if exists treestatus_change_trees;
    drop table if exists treestatus_changes;
    drop table if exists treestatus_log;
    drop table if exists treestatus_trees;
    drop table if exists releng_treestatus_change_trees;
    drop table if exists releng_treestatus_changes;
    drop table if exists releng_treestatus_log;
    drop table if exists releng_treestatus_trees;
  '';
  afterSQL = ''
    alter table treestatus_change_trees rename to releng_treestatus_change_trees;
    alter table treestatus_changes rename to releng_treestatus_changes;
    alter table treestatus_log rename to releng_treestatus_log;
    alter table treestatus_trees rename to releng_treestatus_trees;
  '';

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  project_name = "treestatus/api";
  name = "mozilla-treestatus-api";
  dirname = "treestatus_api";
  src_path = "src/treestatus/api";

  self = mkBackend2 {
    inherit python name dirname src_path project_name;
    inProduction = true;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      (fromRequirementsFile ./../../../lib/cli_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./../../../lib/backend_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./requirements-dev.txt python.packages);
    propagatedBuildInputs =
      (fromRequirementsFile ./requirements.txt python.packages);
    passthru = {
      migrate = mysql2postgresql {
        inherit name beforeSQL afterSQL;
        config = ''
          only_tables:
           - treestatus_change_trees
           - treestatus_changes
           - treestatus_log
           - treestatus_trees
        '';
      };
      update = writeScript "update-${name}" ''
        pushd ${self.src_path}
        ${pypi2nix}/bin/pypi2nix -v \
          -V 3.6 \
          -E "postgresql" \
          -r requirements.txt \
          -r requirements-dev.txt
        popd
      '';
    };
  };

in self
