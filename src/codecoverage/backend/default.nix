{ releng_pkgs
}:

let

  inherit (releng_pkgs.lib) mkBackend fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript redis;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  project_name = "codecoverage/backend";

  self = mkBackend rec {
    inherit python project_name;
    inProduction = true;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit (self) name; };
    buildInputs =
      (fromRequirementsFile ./../../../lib/cli_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./../../../lib/backend_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./requirements-dev.txt python.packages) ++
      [ redis ];
    propagatedBuildInputs =
      (fromRequirementsFile ./requirements.txt python.packages);
    postInstall = ''
      mkdir -p $out/bin
      cp ${src}/launch.sh $out/bin
      chmod +x $out/bin/launch.sh
      cp ${src}/codecoverage_backend/worker.py $out/bin/codecoverage_backend_worker
    '';
    passthru = {
      update = writeScript "update-${self.name}" ''
        pushd ${self.src_path}
        ${pypi2nix}/bin/pypi2nix -v \
          -V 3.6 \
          -r requirements.txt \
          -r requirements-dev.txt
        popd
      '';
    };
    dockerCmd = [
        "launch.sh"
    ];
  };

in self
