{ releng_pkgs
}:

let

  inherit (releng_pkgs.lib) mkTaskclusterHook mkPython2 fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  project_name = "codecoverage-crawler";
  name = "mozilla-code-coverage-crawler";
  dirname = "code_coverage_crawler";

  mkBot = branch:
    let
      cacheKey = "services-" + branch + "-code-coverage-crawler";
      secretsKey = "repo:github.com/mozilla-releng/services:branch:" + branch;
      hook = mkTaskclusterHook {
        name = "Bot for coverage crawler project";
        owner = "mcastelluccio@mozilla.com";
        schedule = [ "0 0 0 * * 0" ]; # every week
        taskImage = self.docker;
        scopes = [
          # Used by taskclusterProxy
          ("secrets:get:" + secretsKey)

          # Email notifications
          "notify:email:mcastelluccio@mozilla.com"
          "notify:email:akhuzyakhmetova@mozilla.com"

          # Used by cache
          ("docker-worker:cache:" + cacheKey)
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
          "/bin/code-coverage-crawler"
          "--taskcluster-secret"
          secretsKey
          "--cache-root"
          "/cache"
        ];
      };
    in
      releng_pkgs.pkgs.writeText "taskcluster-hook-${self.name}.json" (builtins.toJSON hook);

  self = mkPython2 {
    inherit python project_name name dirname;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit name; };
    src_path = "src/codecoverage/crawler";
    buildInputs =
      fromRequirementsFile ./requirements-dev.txt python.packages;
    propagatedBuildInputs =
      fromRequirementsFile ./requirements.txt python.packages;
    passthru = {
      deploy = {
        testing = mkBot "testing";
        staging = mkBot "staging";
        production = mkBot "production";
      };
      update = writeScript "update-${name}" ''
        pushd ${self.src_path}
        ${pypi2nix}/bin/pypi2nix -v \
          -V 3.6 \
          -r requirements.txt \
          -r requirements-dev.txt
        popd
      '';
    };
  };

in self
