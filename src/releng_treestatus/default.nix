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
  releng_common = import ./../../lib/releng_common {
    inherit releng_pkgs python;
    extras = ["api" "auth" "cors" "log" "db" "cache" "security" "pulse"];
  };

  self = mkBackend rec {
    inherit python releng_common;
    production = true;
    name = "releng_treestatus";
    version = fileContents ./../../VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      [ python.packages."flake8"
        python.packages."pytest"
        python.packages."ipdb"
        python.packages."responses"
      ];
    propagatedBuildInputs =
      [ python.packages."Flask"
        python.packages."Flask-Login"
        python.packages."SQLAlchemy"
        python.packages."Werkzeug"
        python.packages."kombu"
        python.packages."pytz"
        python.packages."redis"
      ];
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
        pushd src/${name}
        ${pypi2nix}/bin/pypi2nix -v \
         -V 3.5 \
         -E "postgresql" \
         --setup-requires "six packaging appdirs" \
         -r ../../lib/releng_common/requirements-dev.txt \
         -r requirements.txt \
         -r requirements-dev.txt \
         -r requirements-nix.txt
        popd
      '';
    };
  };

in self
