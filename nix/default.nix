let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json))) {}
}:

let

  releng_pkgs = {

    inherit pkgs;

    lib = import ./lib/default.nix { inherit releng_pkgs; };

    tools = import ./tools/default.nix { inherit releng_pkgs; };

    elmPackages = pkgs.elmPackages.override { nodejs = pkgs."nodejs-6_x"; };

    relengapi_clobberer = import ./../src/relengapi_clobberer { inherit releng_pkgs; };

    relengapi_frontend = import ./../src/relengapi_frontend { inherit releng_pkgs; };

    shipit_dashboard = import ./../src/shipit_dashboard { inherit releng_pkgs; };

    #shipit = import ./../src/shipit { inherit releng_pkgs; };
  };

in releng_pkgs
