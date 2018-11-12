{ releng_pkgs
}:

let

  inherit (releng_pkgs.lib) mkPython3 fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  project_name = "common/naming";

  self = mkPython3 {
    inherit python project_name;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit (self) name; };
    buildInputs =
      (fromRequirementsFile ./requirements-dev.txt python.packages);
    passthru = {
      update = writeScript "update-${self.name}" ''
        pushd ${self.src_path}
        ${pypi2nix}/bin/pypi2nix -v \
          -V 3.6 \
          -r requirements-dev.txt
        popd
      '';
    };
  };

in self
