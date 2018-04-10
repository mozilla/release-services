{ releng_pkgs
}: 

let

  inherit (releng_pkgs.lib) mkBackend mkTaskclusterHook fromRequirementsFile filterSource mysql2postgresql;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  beforeSQL = ''
    DROP TABLE IF EXISTS releng_clobberer_builds;
    DROP TABLE IF EXISTS releng_clobberer_times;
    DROP TABLE IF EXISTS builds;
    DROP TABLE IF EXISTS clobber_times;
  '';
  afterSQL = ''
    ALTER TABLE builds        RENAME TO releng_clobberer_builds;
    ALTER TABLE clobber_times RENAME TO releng_clobberer_times;
  '';

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  name = "mozilla-releng-clobberer";
  dirname = "releng_clobberer";

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
           - builds;
           - clobber_times;
        '';
      };
      update = writeScript "update-${name}" ''
        pushd ${self.src_path}
        ${pypi2nix}/bin/pypi2nix -v \
          -V 3.5 \
          -E "postgresql libffi openssl" \
          -r requirements.txt \
          -r requirements-dev.txt
        popd
      '';
    };
  };

in self
