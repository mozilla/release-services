{ pkgs ? import <nixpkgs> {}
}:

pkgs.stdenv.mkDerivation {
  name = "unpure-example";
  buildInputs = with pkgs; [ jq curl ];
  buildCommand = ''
    if [ "`curl https://rest.ensembl.org/info/ping\?content-type\=application/json | jq .ping`" == "1" ]; then
       echo "WORKS" > $out;
    else
       echo "FAILS" > $out;

    fi
  '';
}
