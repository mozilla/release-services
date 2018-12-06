{ releng_pkgs }:

let
  src = releng_pkgs.pkgs.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./pypi2nix.json));
in
  import src { inherit (releng_pkgs) pkgs; }
