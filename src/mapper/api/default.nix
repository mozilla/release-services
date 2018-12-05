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
  project_name = "mapper/api";

  self = mkBackend {
    inherit python project_name;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit (self) name; };
    buildInputs =
      (fromRequirementsFile ./../../../lib/cli_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./../../../lib/backend_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./requirements-dev.txt python.packages);
    propagatedBuildInputs =
      (fromRequirementsFile ./requirements.txt python.packages);
    dockerCmd = [
      "gunicorn"
      "${self.dirname}.flask:app"
      "--worker-class" "gevent"
      "--log-file"
      "-"
    ];
    passthru = {
      migrate = mysql2postgresql {
        inherit beforeSQL afterSQL;
        inherit (self) name;
        config = ''
          only_tables:
           - projects
           - hashes
        '';
      };
      update = writeScript "update-${self.name}" ''
        pushd ${self.src_path}
        cache_dir=$PWD/../../../tmp/pypi2nix
        mkdir -p $cache_dir
        eval ${pypi2nix}/bin/pypi2nix -v \
          -C $cache_dir \
          -V 3.7 \
          -O ../../../nix/requirements_override.nix \
          -E postgresql \
          -e vcversioner \
          -e pytest-runner \
          -e setuptools-scm \
          -r requirements.txt \
          -r requirements-dev.txt
        popd
      '';
    };
  };

in self
