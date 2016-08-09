let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs_src.json))) {}
}:

let

  elmPackages = pkgs.elmPackages.override { nodejs = pkgs."nodejs-6_x"; };

  from_requirements = files: pkgs':
    map
      (requirement: builtins.getAttr requirement pkgs')
      (pkgs.lib.unique
        (builtins.filter
          (x: x != "" && builtins.substring 0 1 x != "-")
          (pkgs.lib.flatten
            (map
              (file: pkgs.lib.splitString "\n"(pkgs.lib.removeSuffix "\n" (builtins.readFile file)))
              files
            )
          )
        )
      );

  self = {

     relengapi_clobberer = import ./src/relengapi_clobberer { inherit pkgs from_requirements; };

     relengapi_frontend = import ./src/relengapi_frontend { inherit pkgs; };

     #shipit = import ./src/shipit { inherit pkgs from_requirements; };
   };

in self
