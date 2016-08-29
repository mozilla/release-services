{ releng_pkgs
}:

let

  inherit (builtins) fromJSON readFile filterSource attrValues concatStringsSep;
  inherit (releng_pkgs.elmPackages) elm;
  inherit (releng_pkgs.elmPackages.lib) makeElmStuff;
  inherit (releng_pkgs.pkgs) writeScriptBin cacert;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.tools) node2nix elm2nix;

  pkg = fromJSON (readFile ./package.json);
  name = pkg.name;
  version = pkg.version;

  node_modules = import ./package.nix { inherit (releng_pkgs) pkgs; };

  self = mkDerivation {
    name = "${name}-${version}";
    src = filterSource
      (path: type: baseNameOf path != "elm-stuff"
                && baseNameOf path != "node_modules"
                )
      ./.;
    buildInputs = [ elm ] ++ (attrValues node_modules);
    configurePhase = ''
      rm -rf node_modules
      rm -rf elm-stuff
    '' + (makeElmStuff (import ./elm-package.nix)) + ''
      mkdir node_modules
      for item in ${concatStringsSep " " (attrValues node_modules)}; do
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
      cd src/${name}
    '' + self.configurePhase;
    passthru.updateSrc = writeScriptBin "update" ''
      export SSL_CERT_FILE="${cacert}/etc/ssl/certs/ca-bundle.crt"
      pushd src/${name}
      ${node2nix}/bin/node2nix \
        --composition package.nix \
        --input node-packages.json \
        --output node-packages.nix \
        --node-env node-env.nix \
        --flatten \
        --pkg-name nodejs-6_x
      rm -rf elm-stuff
      ${elm}/bin/elm-package install -y
      ${elm2nix}/bin/elm2nix elm-package.nix
      popd
    '';
  };

in self
