{ releng_pkgs
}:

let

  inherit (releng_pkgs) elmPackages;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;

  pkg = builtins.fromJSON (builtins.readFile ./package.json);

  node_package' = (import ./package.nix { inherit (releng_pkgs) pkgs; }).package;
  node_package = node_package'.override (old: {
    src = builtins.filterSource
      (path: type: baseNameOf path == "package.json")
      ./.;
  });

  self = mkDerivation {
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
  };

in self
