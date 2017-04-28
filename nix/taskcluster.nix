let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json))) {}
, taskcluster_secrets
}:

let

  releng_pkgs = import ./default.nix { inherit pkgs; };

in pkgs.stdenv.mkDerivation {
  name = "taskcluster";
  buildInputs = [
    releng_pkgs.tools.taskcluster-tasks
    releng_pkgs.pkgs.curl
    releng_pkgs.pkgs.jq
  ];
  buildCommand = ''
    echo "+--------------------------------------------------------+"
    echo "| Not possible to update repositories using \`nix-build\`. |"
    echo "|         Please run \`nix-shell taskcluster.nix\`.        |"
    echo "+--------------------------------------------------------+"
    exit 1
  '';
  shellHook = ''
    # 1. detect which nix applications need to be rebuilt

    # 2. generate taskcluster tasks (json) for all the tasks that we need to
    #    create

    # 3. create tasks
    mkdir -p tmp
    rm -f tmp/taskcluster_secrets
    curl -L ${taskcluster_secrets} -o tmp/taskcluster_secrets
    taskcluster-tasks \
        --taskcluster-base-url=http://`cat /etc/hosts | grep taskcluster | awk '{ print $1 }'` \
        --docker-username=`cat tmp/taskcluster_secrets | jq -r '.secret.DOCKER_USERNAME'` \
        --docker-password=`cat tmp/taskcluster_secrets | jq -r '.secret.DOCKER_PASSWORD'`
    exit
  '';
}
