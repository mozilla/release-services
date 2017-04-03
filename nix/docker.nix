let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json))) {}
}:

let

  releng_pkgs = import ./default.nix { inherit pkgs; };

  inherit (releng_pkgs.lib) packagesWith mkDocker;

in builtins.listToAttrs 
     (map ({ name, pkg }: { inherit name; value = pkg.docker; })
          (packagesWith "docker" releng_pkgs)
     )
