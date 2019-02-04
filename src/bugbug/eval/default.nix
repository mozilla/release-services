{ releng_pkgs
}:

let

  inherit (releng_pkgs.lib) mkTaskclusterHook mkPython fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript makeWrapper fetchurl;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) fileContents optional licenses;
  inherit (releng_pkgs.tools) pypi2nix mercurial;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  project_name = "bugbug/eval";

  mkBot = branch:
    let
      cacheKey = "services-" + branch + "-bugbug-eval";
      secretsKey = "repo:github.com/mozilla-releng/services:branch:" + branch;
      hook = mkTaskclusterHook {
        name = "Bot performing evaluation for Bugzilla ML";
        owner = "mcastelluccio@mozilla.com";
        # XXX: schedule = [ "0 0 * * * *" ];  # every month
        taskImage = self.docker;
        scopes = [
          # Used by taskclusterProxy
          ("secrets:get:" + secretsKey)

          # Used by cache
          ("docker-worker:cache:" + cacheKey)

          # Needed to index the task in the TaskCluster index
          ("index:insert-task:project.releng.services.project." + branch + ".bugbug_eval.*")
        ];
        cache = {
          "${cacheKey}" = "/cache";
        };
        taskEnv = {
          "SSL_CERT_FILE" = "${releng_pkgs.pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
          "APP_CHANNEL" = branch;
        };
        taskCapabilities = {};
        taskCommand = [
          "/bin/bugbug-eval"
          "--taskcluster-secret"
          secretsKey
          "--cache-root"
          "/cache"
        ];
        workerType = "releng-svc-compute";
        taskArtifacts = {
          "public/bug.json" = {
            type = "file";
            path = "/bug.json";
          };
          "public/regression.json" = {
            type = "file";
            path = "/regression.json";
          };
          "public/tracking.json" = {
            type = "file";
            path = "/tracking.json";
          };
        };
      };
    in
      releng_pkgs.pkgs.writeText "taskcluster-hook-${self.name}.json" (builtins.toJSON hook);

  self = mkPython {
    inherit python project_name;
    inProduction = true;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit(self) name; };
    buildInputs =
      (fromRequirementsFile ./../../../lib/cli_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./requirements-dev.txt python.packages);
    propagatedBuildInputs =
      (fromRequirementsFile ./requirements.txt python.packages);
    postInstall = ''
      mkdir -p $out/bin
      ln -s ${mercurial}/bin/hg $out/bin
    '';
		shellHook = ''
			export PATH="${mercurial}/bin:$PATH"
		'';
    passthru = {
      deploy = {
        testing = mkBot "testing";
        staging = mkBot "staging";
        production = mkBot "production";
      };
      update = writeScript "update-${self.name}" ''
        pushd ${self.src_path}
        cache_dir=$PWD/../../../tmp/pypi2nix
        mkdir -p $cache_dir
        ${pypi2nix}/bin/pypi2nix -v \
          -C $cache_dir \
          -V 3.7 \
          -O ../../../nix/requirements_override.nix \
          -E blas \
          -E gfortran \
          -E libffi \
          -E openssl \
          -E pkgconfig \
          -E freetype.dev \
          -E libjpeg.dev \
          -s numpy \
          -s flit \
          -s intreehooks \
          -s cython \
          -e pytest-runner \
          -e setuptools-scm \
          -r requirements.txt \
          -r requirements-dev.txt
        popd
      '';
    };
  };

in self
