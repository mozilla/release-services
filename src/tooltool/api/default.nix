{ releng_pkgs
}:

let

  inherit (releng_pkgs.lib) mkBackend3 mkTaskclusterHook fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript writeText dockerTools;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  project_name = "tooltool/api";
  version = fileContents ./VERSION;

  mkCronJob = { schedule, command }:
    builtins.listToAttrs (
      map (channel:
        { name = channel;
          value =
            let
              hook_name = "${self.name}_${command}_${channel}";
              hook = mkTaskclusterHook {
                name = hook_name;
                owner = "rgarbas@mozilla.com";
                inherit schedule;
                scopes =
                  [ "secrets:get:repo:github.com/mozilla-releng/services:branch:${channel}"
                    "queue:create-task:aws-provisioner-v1/releng-svc"
                  ];
                taskImage = self.docker;
                taskEnv = {
                  TASKCLUSTER_SECRET = "repo:github.com/mozilla-releng/services:branch:${channel}";
                };
                taskCapabilities = {};
                taskCommand = [
                  "/bin/flask"
                  command
                ];
                deadline = "4 hours";
                maxRunTime = 4 * 60 * 60;
                workerType = "releng-svc";
              };
            in
              writeText "taskcluster-hook-${hook_name}.json" (builtins.toJSON hook);
        }) ["testing" "staging" "production"]);

  self = mkBackend3 {
    inherit python version project_name;
    inStaging = true;
    inProduction = true;
    src = filterSource ./. { inherit(self) name; };
    buildInputs =
      (fromRequirementsFile ./../../../lib/cli_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./../../../lib/backend_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./requirements-dev.txt python.packages);
    propagatedBuildInputs =
      (fromRequirementsFile ./requirements.txt python.packages);
    passthru = {
      cron = {
        check_pending_uploads = mkCronJob { schedule = [ "*/10 * * * *" ];  # every 10 min;
                                            command = "check-pending-uploads";
                                          };
        replicate = mkCronJob { schedule = [ "0 * * * *" ];  # every 1 hour;
                                command = "replicate";
                              };
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
