{ releng_pkgs
}:

let

  inherit (releng_pkgs.lib) mkBackend3 fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  project_name = "tokens/api";

  self = mkBackend3 {
    inherit python project_name;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit(self) name; };
    inStaging = true;
    inProduction = true;
    buildInputs =
      (fromRequirementsFile ./../../../lib/cli_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./../../../lib/backend_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./requirements-dev.txt python.packages);
    propagatedBuildInputs =
      (fromRequirementsFile ./requirements.txt python.packages);
    passthru = {
      update = writeScript "update-${self.name}" ''
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
