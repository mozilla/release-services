{ releng_pkgs
}:

let

  inherit (releng_pkgs.lib) mkPython fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  project_name = "common/naming";

  self = mkPython {
    inherit python project_name;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit (self) name; };
    buildInputs =
      (fromRequirementsFile ./requirements-dev.txt python.packages);
    passthru = {
      update = writeScript "update-${self.name}" ''
        pushd ${self.src_path}
        cache_dir=$PWD/../../../tmp/pypi2nix
        mkdir -p $cache_dir
        eval ${pypi2nix}/bin/pypi2nix -v \
          -C $cache_dir \
          -V 3.7 \
          -O ../../../nix/requirements_override.nix \
          -e pytest-runner \
          -e setuptools-scm \
          -r requirements-dev.txt
        popd
      '';
    };
  };

in self
