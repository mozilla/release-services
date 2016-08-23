{ releng_pkgs }:

let

  node2nixSrc = releng_pkgs.pkgs.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./node2nix.json));

  node2nix =
    (import "${node2nixSrc}/default.nix" {
      inherit (releng_pkgs) pkgs;
      inherit (releng_pkgs.pkgs.stdenv) system;
    });

in node2nix.package
