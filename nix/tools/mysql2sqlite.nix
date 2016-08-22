{ releng_pkgs }:

let

  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs) fetchFromGitHub;

  rev = "1b0b5d610c6090422625a2c58d2c23d2296eab3a";

in mkDerivation {
  name = "mysql2sqlite-2016-08-22-${rev}";
  src = fetchFromGitHub {
    owner = "dumblob";
    repo = "mysql2sqlite";
    inherit rev;
    sha256= "0ygchrq25kkb2brkmy7j5g3rgdlj5f72lz7h9zdcvxcqjj9ms2dl";
  };
  buildInputs = [ releng_pkgs.pkgs.gawk ];
  installPhase = ''
    mkdir -p $out/bin
    cp mysql2sqlite $out/bin
    chmod +x $out/bin/mysql2sqlite
  '';
}
