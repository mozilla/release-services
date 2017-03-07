{ releng_pkgs
}: 

let

  inherit (releng_pkgs.lib) mkBackend fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  name = "mozilla-releng-tooltool";
  dirname = "releng_tooltool";

  self = mkBackend rec {
    inherit python name dirname;
    version = fileContents ./../../VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      fromRequirementsFile ./requirements-dev.txt python.packages;
    propagatedBuildInputs =
      fromRequirementsFile ./requirements.txt python.packages;
    passthru = {
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
