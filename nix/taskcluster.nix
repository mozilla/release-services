let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json))) {}
}:

let

  releng_pkgs = import ./default.nix { inherit pkgs; };

  inherit (releng_pkgs.lib) packagesWith;
  inherit (releng_pkgs.pkgs.lib) flatten;

  append2Spaces= text:
    pkgs.lib.strings.concatStringsSep "\n" (
      map (x: "  " + x) (pkgs.lib.splitString "\n" text)
    );

  tasks =
    append2Spaces (
      pkgs.lib.strings.concatStringsSep "\n\n" (
        flatten (map (pkg: pkg.taskclusterGithubTasks)
                     (packagesWith  "taskclusterGithubTasks"  releng_pkgs)
                )
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
