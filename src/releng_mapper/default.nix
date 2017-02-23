{ releng_pkgs
}: 

let

  inherit (releng_pkgs.lib) mkBackend filterSource mysql2postgresql;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  beforeSQL = ''
    DROP TABLE IF EXISTS projects;
    DROP TABLE IF EXISTS hashes;
    DROP TABLE IF EXISTS releng_mapper_projects;
    DROP TABLE IF EXISTS releng_mapper_hashes;
  '';
  afterSQL = ''
    ALTER TABLE projects RENAME TO releng_mapper_projects;
    ALTER TABLE hashes RENAME TO releng_mapper_hashes;
  '';

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  releng_common = import ./../../lib/releng_common {
    inherit releng_pkgs python;
    extras = ["api" "auth" "cors" "log" "db" ];
  };

  self = mkBackend rec {
    inherit python releng_common;
    name = "releng_mapper";
    version = fileContents ./../../VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      [ python.packages."flake8"
        python.packages."pytest"
        python.packages."ipdb"
      ];
    propagatedBuildInputs =
      [];
    passthru = {
      migrate = mysql2postgresql {
        inherit name beforeSQL afterSQL;
        config = ''
          only_tables:
           - projects
           - hashes
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
