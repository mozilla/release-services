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

    releng_docs = import ./../src/releng_docs { inherit releng_pkgs; };
    releng_frontend = import ./../src/releng_frontend { inherit releng_pkgs; };
    releng_clobberer = import ./../src/releng_clobberer { inherit releng_pkgs; };

    shipit_frontend = import ./../src/shipit_frontend { inherit releng_pkgs; };
    shipit_dashboard = import ./../src/shipit_dashboard { inherit releng_pkgs; };

  };

in releng_pkgs
