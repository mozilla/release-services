{ releng_pkgs }:

let

  pypi2nixSrc = releng_pkgs.pkgs.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./pypi2nix.json));
  pypi2nixRelease = import "${pypi2nixSrc}/release.nix" { pypi2nix = pypi2nixSrc; };

in
  builtins.getAttr
    releng_pkgs.pkgs.stdenv.system
    pypi2nixRelease.build
