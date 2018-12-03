{ releng_pkgs
}:

let

  inherit (releng_pkgs.lib) mkBackend fromRequirementsFile filterSource mkDocker mkDockerflow;
  inherit (releng_pkgs.pkgs) writeScript git busybox;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  project_name = "shipit/api";

  self = mkBackend {
    inherit python project_name;
    inProduction = false;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit (self) name; };
    buildInputs =
      (fromRequirementsFile ./../../../lib/cli_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./../../../lib/backend_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./requirements-dev.txt python.packages);
    propagatedBuildInputs =
      [ git ] ++
      (fromRequirementsFile ./requirements.txt python.packages);
    postInstall = ''
      mkdir -p $out/bin
      ln -s ${git}/bin/git $out/bin/git
    '';
    passthru = {
      worker_docker = mkDocker {
        inherit (self.config) version;
        inherit (self) name;
        contents = [ busybox self ] ++ self.config.dockerContents;
        config = self.docker_default_config;
      };
      worker_dockerflow = mkDockerflow {
        inherit (self.config) version src;
        inherit (self) name;
        fromImage = self.worker_docker;
        Cmd = ["flask" "worker"];
      };
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
