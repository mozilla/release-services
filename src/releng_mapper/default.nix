{ releng_pkgs
}: 

let

  inherit (releng_pkgs.lib) mkBackend fromRequirementsFile filterSource mysql2postgresql;
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
  name = "mozilla-releng-mapper";
  dirname = "releng_mapper";

  self = mkBackend {
    inherit python name dirname;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      (fromRequirementsFile ./../../lib/cli_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./../../lib/backend_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./requirements-dev.txt python.packages);
    propagatedBuildInputs =
      (fromRequirementsFile ./requirements.txt python.packages);
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
        pushd ${self.src_path}
        ${pypi2nix}/bin/pypi2nix -v \
          -V 3.5 \
          -E "postgresql" \
          -r requirements.txt \
          -r requirements-dev.txt
        popd
      '';
    };
  };

in self
