let
  pkgs' = import <nixpkgs> {};
  nixpkgs = pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json));
in
{ pkgs ? import nixpkgs {}
}:

let

  postgresql = pkgs.postgresql95;

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
    postgresql = pkgs.postgresql95;

    # TODO: releng_common_example = import ./../lib/releng_common/example { inherit releng_pkgs; };
    elm_common_example = import ./../lib/elm_common/example { inherit releng_pkgs; };

    releng_docs = import ./../src/releng_docs { inherit releng_pkgs; };
    releng_frontend = import ./../src/releng_frontend { inherit releng_pkgs; };
    releng_clobberer = import ./../src/releng_clobberer { inherit releng_pkgs; };
    releng_tooltool = import ./../src/releng_tooltool { inherit releng_pkgs; };
    releng_treestatus = import ./../src/releng_treestatus { inherit releng_pkgs; };
    releng_mapper = import ./../src/releng_mapper { inherit releng_pkgs; };
    releng_archiver = import ./../src/releng_archiver { inherit releng_pkgs; };

    shipit_frontend = import ./../src/shipit_frontend { inherit releng_pkgs; };
    shipit_dashboard = import ./../src/shipit_dashboard { inherit releng_pkgs; };
    shipit_bot_uplift = import ./../src/shipit_bot_uplift { inherit releng_pkgs; };
    shipit_pipeline = import ./../src/shipit_pipeline { inherit releng_pkgs; };
    shipit_signoff = import ./../src/shipit_signoff { inherit releng_pkgs; };

  };

in releng_pkgs
