let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json))) {}
, taskcluster_secrets ? ""
, tasks_group_id ? ""
}:

let

  inherit (releng_pkgs.lib) packagesWith;
  inherit (releng_pkgs.pkgs.lib) flatten concatStringsSep;

  releng_pkgs =
    import ./default.nix { inherit pkgs; };

  apps = {
    releng-docs = releng_pkgs.apps.releng-docs;
    shipit-static-analysis = releng_pkgs.apps.shipit-static-analysis;
    shipit-code-coverage = releng_pkgs.apps.shipit-code-coverage;
  };

in pkgs.stdenv.mkDerivation {
  name = "taskcluster";
  buildInputs = [
    releng_pkgs.tools.taskcluster-cli
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

    mkdir -p tmp

    echo "1/5: Retriving secrets (${taskcluster_secrets})" 
    rm -f tmp/taskcluster_secrets.json
    #curl -L ${taskcluster_secrets} -o tmp/taskcluster_secrets.json


    echo "2/5: Checking cache which application needs to be built" 
    APPS=
    for app in ${concatStringsSep " " (builtins.attrNames apps)}; do
      echo -n "  => $app: "
      exists=`taskcluster check-cache $app`
      echo $exists
      if [ "$exists" = "NOT EXISTS" ]; then
         APPS="$APPS $app"
      fi
    done


    echo "3/5: Creating taskcluster tasks definitions (./tmp/tasks.json)"
    rm -f tmp/tasks.json
    echo "{}" > tmp/tasks.json
    for app in $APPS; do
      echo -n "  => $app: "
      echo "GENERATED"
    done

    exit 123
    echo "3/5: Generating taskcluster tasks definitions" 
    rm -f tmp/tasks.json


    cat ./tmp/tasks.json

    taskcluster tasks \
      --taskcluster-client-id="mozilla-ldap/rgarbas@mozilla.com/test" \
      --taskcluster-access-token="d6NFmqPgS7KCggMca_MVBAIMMx2n07RVGIY83J1EhEpg" \
      --docker-repo="mozillareleng/services" \
      --docker-username="mozillarelengservices" \
      --docker-password="tSXDhLIwvCnoZGtIyaTFJt3DxFwU7M5cmgvh4aoR3YAObL9Qn5" \
      --tasks-file=tmp/tasks.json

    #taskcluster-tasks \
    #    --taskcluster-base-url=http://`cat /etc/hosts | grep taskcluster | awk '{ print $1 }'` \
    #    --docker-username=`cat tmp/taskcluster_secrets | jq -r '.secret.DOCKER_USERNAME'` \
    #    --docker-password=`cat tmp/taskcluster_secrets | jq -r '.secret.DOCKER_PASSWORD'`

    # never enter nix-shell
    exit
  '';
}
