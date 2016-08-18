let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json))) {}
, pkg ? null
}:

let

  releng_pkgs = import ./default.nix {};

  pkgsUpdates = {
    # TODO: nixpkgs = ...
    tools = ''
      pushd nix/
      pypi2nix -v \
        -V 3.5 \
        -r requirements.txt 
      popd
    '';
    relengapi_clobberer = ''
      pushd src/relengapi_clobberer
      pypi2nix -v \
        -V 3.5 \
        -E "postgresql" \
        -r requirements.txt \
        -r requirements-setup.txt \
        -r requirements-dev.txt \
        -r requirements-prod.txt 
      popd
    '';
    relengapi_frontend = ''
      pushd src/relengapi_frontend
      node2nix \
        --composition package.nix \
        --input node-packages.json \
        --output node-packages.nix \
        --node-env node-env.nix \
        --flatten \
        --pkg-name nodejs-6_x
      rm -rf elm-stuff
      elm-package install -y
      elm2nix elm-package.nix
      popd
    '';
    shipit_dashboard = ''
      pushd src/shipit_dashboard
      pypi2nix -v \
        -V 3.5 \
        -E "postgresql" \
        -r requirements.txt \
        -r requirements-setup.txt \
        -r requirements-dev.txt \
        -r requirements-prod.txt 
      popd
    '';
  };

in pkgs.stdenv.mkDerivation {
  name = "update-releng";
  buildInputs = [
    releng_pkgs.elmPackages.elm
    releng_pkgs.tools.elm2nix
    releng_pkgs.tools.node2nix
    # TODO: releng_pkgs.tools.pypi2nix
  ];
  buildCommand = ''
    echo "+--------------------------------------------------------+"
    echo "| Not possible to update repositories using \`nix-build\`. |"
    echo "|         Please run \`nix-shell update.nix\`.             |"
    echo "+--------------------------------------------------------+"
    exit 1
  '';
  shellHook = ''
    export SSL_CERT_FILE="${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
  '' + (
    if pkg == null
    then builtins.concatStringsSep "\n\n" (builtins.attrValues pkgsUpdates)
    else builtins.getAttr pkg pkgsUpdates
  ) + ''
    echo "Packages updated!"
    exit
  '';
}
