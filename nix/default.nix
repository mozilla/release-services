let
  pkgs' = import <nixpkgs> {};
  nixpkgs = pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json));
in
{ pkgs ? import nixpkgs {}
}:

let

  releng_pkgs = {

    inherit pkgs;

    nixpkgs = nixpkgs // {
      name = "nixpkgs-2016-08-23";
      updateSrc = releng_pkgs.lib.updateFromGitHub {
        owner = "garbas";
        repo = "nixpkgs";
        branch = "python-srcs";
        path = "nix/nixpkgs.json";
      };
    };

    lib = import ./lib/default.nix { inherit releng_pkgs; };

    tools = import ./tools/default.nix { inherit releng_pkgs; };

    elmPackages = pkgs.elmPackages.override { nodejs = pkgs."nodejs-6_x"; };

    releng_docs = import ./../docs { inherit releng_pkgs; };

    relengapi_clobberer = import ./../src/relengapi_clobberer { inherit releng_pkgs; };

    relengapi_frontend = import ./../src/relengapi_frontend { inherit releng_pkgs; };

    shipit_dashboard = import ./../src/shipit_dashboard { inherit releng_pkgs; };

    #shipit = import ./../src/shipit { inherit releng_pkgs; };
  };

in releng_pkgs
