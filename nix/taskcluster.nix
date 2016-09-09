let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json))) {}
}:

let
  createTask =
    { name
    , branch
    , secrets ? "garbage/garbas/temp-releng-services-${branch}"
    }:
    ''
    - metadata:
        name: "${name}"
        description: "Test, build and deploy ${name}"
        owner: "{{ event.head.user.email }}"
        source: "https://github.com/mozilla-releng/services/tree/${branch}/src/${name}"
      scopes:
        - secrets:get:${secrets}
      extra:
        github:
          env: true
          events:
            ${if branch == "staging" || branch == "production"
              then "- push"
              else "- pull_request.*\n        - push"}
          branches:
            - ${branch}
      provisionerId: "{{ taskcluster.docker.provisionerId }}"
      workerType: "{{ taskcluster.docker.workerType }}"
      payload:
        maxRunTime: 7200 # seconds (i.e. two hours)
        image: "nixos/nix:latest"
        features:
          taskclusterProxy: true
        env:
          APP: "releng_docs"
          TASKCLUSTER_SECRETS: "taskcluster/secrets/v1/secret/${secrets}"
        command:
          - "/bin/bash"
          - "-c"
          - "nix-env -iA nixpkgs.gnumake nixpkgs.curl && mkdir /src && cd /src && curl -L https://github.com/mozilla-releng/services/archive/$GITHUB_HEAD_SHA.tar.gz -o $GITHUB_HEAD_SHA.tar.gz && tar zxf $GITHUB_HEAD_SHA.tar.gz && cd services-$GITHUB_HEAD_SHA && ./.taskcluster.sh"
  '';

  releng = ["frontend" "docs" "clobberer"];
  shipit = ["frontend" "dashboard"];

  append2lines = text:
    pkgs.lib.strings.concatStringsSep "\n" (
      map (x: "  " + x) (pkgs.lib.splitString "\n" text));

  tasks =
    pkgs.lib.strings.concatStringsSep "\n" (
      map append2lines (
        (map (x: createTask { name = "releng_" + x; branch = "master"; }) releng) ++
        (map (x: createTask { name = "releng_" + x; branch = "staging"; }) releng) ++
        (map (x: createTask { name = "releng_" + x; branch = "production"; }) releng) ++
        (map (x: createTask { name = "shipit_" + x; branch = "master"; }) shipit) ++
        (map (x: createTask { name = "shipit_" + x; branch = "staging"; }) shipit) ++
        (map (x: createTask { name = "shipit_" + x; branch = "production"; }) shipit) ++
        []
      )
    );

in pkgs.writeText "taskcluster.yml" ''
version: 0
metadata:
  name: "Mozilla RelEng"
  description: "Mozilla RelEng Services"
  owner: "{{ event.head.user.email }}"
  source: "{{ event.head.repo.url }}"
tasks:

${tasks}
''
