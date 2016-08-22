{ releng_pkgs }:

let

  node2nixSrc = releng_pkgs.pkgs.fetchFromGitHub {
    owner = "svanderburg";
    repo = "node2nix";
    rev = "c973ef418d94311031b84552527c4e1390dc69c8";
    sha256 = "1iq0d6rv0g72kxpas3yrrcnjfsr5gk5jf2z4x9lmyqms89aj2x4g";
  };

  node2nix =
    (import "${node2nixSrc}/default.nix" {
      inherit (releng_pkgs) pkgs;
      inherit (releng_pkgs.pkgs.stdenv) system;
    });

in node2nix.package
