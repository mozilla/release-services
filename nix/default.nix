let
  pkgs' = import <nixpkgs> {};
  nixpkgs = pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json));
in
{ pkgs ? import nixpkgs {}
}:

let

  releng_pkgs = {

    pkgs = pkgs // {
      name = "nixpkgs";
      update = releng_pkgs.lib.updateFromGitHub {
        owner = "NixOS";
        repo = "nixpkgs-channels";
        branch = "nixos-unstable";
        path = "nix/nixpkgs.json";
      };
    };

    lib = import ./lib/default.nix { inherit releng_pkgs; };
    tools = import ./tools/default.nix { inherit releng_pkgs; };
    elmPackages = pkgs.elmPackages.override { nodejs = pkgs."nodejs-6_x"; };

    releng_docs = import ./../src/releng_docs { inherit releng_pkgs; };
    releng_frontend = import ./../src/releng_frontend { inherit releng_pkgs; };
    releng_clobberer = import ./../src/releng_clobberer { inherit releng_pkgs; };
    releng_tooltool = import ./../src/releng_tooltool { inherit releng_pkgs; };
    releng_treestatus= import ./../src/releng_treestatus { inherit releng_pkgs; };
    releng_mapper = import ./../src/releng_mapper { inherit releng_pkgs; };
    releng_archiver = import ./../src/releng_archiver { inherit releng_pkgs; };

    shipit_frontend = import ./../src/shipit_frontend { inherit releng_pkgs; };
    shipit_dashboard = import ./../src/shipit_dashboard { inherit releng_pkgs; };
    shipit_workflow = import ./../src/shipit_workflow { inherit releng_pkgs; };

  };

in releng_pkgs
