{ releng_pkgs }:

releng_pkgs.pkgs.stdenv.mkDerivation {
  name = "elm2nix";
  buildInputs = [ releng_pkgs.pkgs.ruby ];
  buildCommand = ''
    mkdir -p $out/bin
    cp ${releng_pkgs.pkgs.path}/pkgs/development/compilers/elm/elm2nix.rb $out/bin/elm2nix
    sed -i -e "s|\"package.nix\"|ARGV[0]|" $out/bin/elm2nix
    chmod +x $out/bin/elm2nix
    patchShebangs $out/bin
  '';
}
