{ releng_pkgs
}:

let

  inherit (releng_pkgs) elmPackages;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;

  pkg = builtins.fromJSON (builtins.readFile ./package.json);
  node_modules = import ./package.nix { inherit (releng_pkgs) pkgs; };

  self = mkDerivation {
    name = "${pkg.name}-${pkg.version}";
    src = builtins.filterSource
      (path: type: baseNameOf path != "elm-stuff"
                && baseNameOf path != "node_modules"
                )
      ./.;
    buildInputs = [ elmPackages.elm ] ++ (builtins.attrValues node_modules);
    configurePhase = elmPackages.lib.makeElmStuff (import ./elm-package.nix) + ''
      rm -rf node_modules
      mkdir node_modules
      for item in ${builtins.concatStringsSep " " (builtins.attrValues node_modules)}; do
        ln -s $item/lib/node_modules/* ./node_modules
      done
    '';
    buildPhase = ''
      neo build --config webpack.config.js
    '';
    installPhase = ''
      mkdir $out
      cp build/* $out/ -R
    '';
    shellHook = ''
      cd src/${pkg.name}
    '' + self.configurePhase;
  };

in self
