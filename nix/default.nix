let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json))) {}
}:

let

  python_tools = import ./requirements.nix {
    inherit pkgs;
  };

  node2nixSrc = pkgs.fetchFromGitHub {
    owner = "svanderburg";
    repo = "node2nix";
    rev = "c973ef418d94311031b84552527c4e1390dc69c8";
    sha256 = "1iq0d6rv0g72kxpas3yrrcnjfsr5gk5jf2z4x9lmyqms89aj2x4g";
  };

  releng_pkgs = {

    inherit pkgs;

    tools = {

      awscli = python_tools.packages."awscli";
      aws-shell = python_tools.packages."aws-shell";

      node2nix =
        (import "${node2nixSrc}/default.nix" {
          inherit pkgs;
          inherit (pkgs.stdenv) system;
        }).package;

      elm2nix = pkgs.stdenv.mkDerivation {
        name = "elm2nix";
        buildInputs = [ pkgs.ruby ];
        buildCommand = ''
          mkdir -p $out/bin
          cp ${<nixpkgs/pkgs/development/compilers/elm/elm2nix.rb>} $out/bin/elm2nix
          sed -i -e "s|\"package.nix\"|ARGV[0]|" $out/bin/elm2nix
          chmod +x $out/bin/elm2nix
          patchShebangs $out/bin
        '';
      };

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
