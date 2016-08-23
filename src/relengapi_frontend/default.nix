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
    configurePhase = ''
      rm -rf node_modules
      rm -rf elm-stuff
    '' + elmPackages.lib.makeElmStuff (import ./elm-package.nix) + ''
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
    passthru.updateSrc = releng_pkgs.pkgs.writeScriptBin "update" ''
      export SSL_CERT_FILE="${releng_pkgs.pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
      pushd src/relengapi_frontend
      ${releng_pkgs.tools.node2nix}/bin/node2nix \
        --composition package.nix \
        --input node-packages.json \
        --output node-packages.nix \
        --node-env node-env.nix \
        --flatten \
        --pkg-name nodejs-6_x
      rm -rf elm-stuff
      ${elmPackages.elm}/bin/elm-package install -y
      ${releng_pkgs.tools.elm2nix}/bin/elm2nix elm-package.nix
      popd
    '';
  };

in self
