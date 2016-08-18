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

  ignoreRequirementsLines = specs:
    builtins.filter
      (x: x != "" &&                         # ignore all empty lines
          builtins.substring 0 1 x != "-" && # ignore all -r/-e
          builtins.substring 0 1 x != "#"    # ignore all comments
      )
      specs;

  cleanRequirementsSpecification = specs:
    let
      separators = [ "==" "<=" ">=" ">" "<" ];
      removeVersion = spec:
        let
          possible_specs =
            pkgs.lib.unique
              (builtins.filter
                (x: x != null)
                (map
                  (separator:
                    let
                      spec' = pkgs.lib.splitString separator spec;
                    in
                      if builtins.length spec' != 1
                      then builtins.head spec'
                      else null
                  )
                  separators
                )
              );
        in
          if builtins.length possible_specs == 1
          then builtins.head possible_specs
          else spec;
    in
      map removeVersion specs;


  releng_pkgs = {

    inherit pkgs;

    from_requirements = files: pkgs':
      let
        # read all files and flatten the dependencies
        # TODO: read recursivly all -r statements
        specs =
          pkgs.lib.flatten
            (map
              (file: pkgs.lib.splitString "\n"(pkgs.lib.removeSuffix "\n" (builtins.readFile file)))
              files
            );
      in
        map
          (requirement: builtins.getAttr requirement pkgs')
          (pkgs.lib.unique
            (cleanRequirementsSpecification
              (ignoreRequirementsLines
                specs
              )
            )
          );

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

    elmPackages = pkgs.elmPackages.override { nodejs = pkgs."nodejs-6_x"; };

    relengapi_clobberer = import ./../src/relengapi_clobberer { inherit releng_pkgs; };

    relengapi_frontend = import ./../src/relengapi_frontend { inherit releng_pkgs; };

    shipit_dashboard = import ./../src/shipit_dashboard { inherit releng_pkgs; };

    #shipit = import ./../src/shipit { inherit releng_pkgs; };
  };

in releng_pkgs
