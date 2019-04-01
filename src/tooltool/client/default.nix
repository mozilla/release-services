{ releng_pkgs
}:

let

  inherit (releng_pkgs.lib) mkPython mkTaskclusterHook fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript writeText dockerTools;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  project_name = "tooltool/client";
  version = fileContents ./VERSION;

  self = mkPython {
    inherit python version project_name;
    inStaging = true;
    inProduction = true;
    src = filterSource ./. { inherit(self) name; };
    buildInputs =
      with releng_pkgs.pkgs; [ zip which ] ++
      (fromRequirementsFile ./requirements-dev.txt python.packages);
    propagatedBuildInputs =
      (fromRequirementsFile ./requirements.txt python.packages);
    checkPhase = ''
      sh validate.sh
    '';
    passthru = {
      update = writeScript "update-${self.name}" ''
        pushd ${self.src_path}
        cache_dir=$PWD/../../../tmp/pypi2nix
        mkdir -p $cache_dir
        eval ${pypi2nix}/bin/pypi2nix -v \
          -C $cache_dir \
          -V 2.7 \
          -O ../../../nix/requirements_override.nix \
          -r requirements.txt \
          -r requirements-dev.txt
        popd
      '';
    };
  };

in self

