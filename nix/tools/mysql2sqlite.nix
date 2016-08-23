{ releng_pkgs }:

let

  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs) fetchFromGitHub;

in mkDerivation {
  name = "mysql2sqlite-2016-08-22";
  src = fetchFromGitHub (builtins.fromJSON (builtins.readFile ./mysql2sqlite.json));
  buildInputs = [ releng_pkgs.pkgs.gawk ];
  installPhase = ''
    mkdir -p $out/bin
    cp mysql2sqlite $out/bin
    chmod +x $out/bin/mysql2sqlite
  '';
}
