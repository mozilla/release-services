{ releng_pkgs }:

let

  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs) fetchFromGitHub;

in mkDerivation {
}
