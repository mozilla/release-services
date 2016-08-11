let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json))) {}
}:

let

  python_tools = import ./requirements.nix {
    inherit pkgs;
  };

  releng_pkgs = {

    inherit pkgs;

    tools = {
      awscli = python_tools.packages."awscli";
      aws-shell = python_tools.packages."aws-shell";
    };

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

    elmPackages = pkgs.elmPackages.override { nodejs = pkgs."nodejs-6_x"; };

    relengapi_clobberer = import ./../src/relengapi_clobberer { inherit releng_pkgs; };

    relengapi_frontend = import ./../src/relengapi_frontend { inherit releng_pkgs; };

    #shipit = import ./../src/shipit { inherit releng_pkgs; };
  };

in releng_pkgs
