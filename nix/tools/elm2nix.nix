{ pkgs }:

pkgs.stdenv.mkDerivation {
  name = "elm2nix";
  buildInputs = [ pkgs.ruby ];
  buildCommand = ''
    mkdir -p $out/bin
    cp ${pkgs.path}/pkgs/development/compilers/elm/elm2nix.rb $out/bin/elm2nix
    sed -i -e "s|\"package.nix\"|ARGV[0]|" $out/bin/elm2nix
    chmod +x $out/bin/elm2nix
    patchShebangs $out/bin
  '';
}
