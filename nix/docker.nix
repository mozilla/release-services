let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json))) {}
}:

let

  releng_pkgs = import ./default.nix { inherit pkgs; };

  inherit (releng_pkgs.lib) packagesWith mkDocker;

in builtins.listToAttrs 
     (map (pkg: { name = (builtins.parseDrvName pkg.name).name;
                  value = pkg.docker;
                })
          (packagesWith "docker" releng_pkgs)
     )
