{ pkgs ? import <nixpkgs> {}
, elmPackages ? pkgs.elmPackages
}:

let
  pkg = builtins.fromJSON (builtins.readFile ./package.json);
  node_package' = (import ./package.nix { inherit pkgs; }).package;
  node_package = node_package'.override (old: {
    src = builtins.filterSource
      (path: type: baseNameOf path == "package.json")
      ./.;
  });
in pkgs.stdenv.mkDerivation {
  name = "${pkg.name}-${pkg.version}";
  src = builtins.filterSource
    (path: type: baseNameOf path != "elm-stuff"
              && baseNameOf path != "node_modules"
              )
    ./.;
  preConfigure = elmPackages.lib.makeElmStuff (import ./elm-package.nix);
  buildInputs = [ node_package elmPackages.elm ];
  buildPhase = ''
    ln -s ${node_package}/lib/node_modules/relengapi_frontend/node_modules ./
    ./node_modules/.bin/neo build
  '';
  installPhase = ''
    mkdir $out
    cp build/* $out/ -R
  '';
}
