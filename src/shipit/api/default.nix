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
