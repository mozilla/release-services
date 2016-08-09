let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs_src.json))) {}
, pkg ? null
}:

let

  elm2nix = pkgs.stdenv.mkDerivation {
    name = "elm2nix";
    buildInputs = [ pkgs.ruby ];
    buildCommand = ''
      mkdir -p $out/bin
      cp ${<nixpkgs/pkgs/development/compilers/elm/elm2nix.rb>} $out/bin/elm2nix
      sed -i -e "s|\"package.nix\"|ARGV[0]|" $out/bin/elm2nix
      chmod +x $out/bin/elm2nix
      patchShebangs $out/bin
    '';
  };

  elmPackages = pkgs.elmPackages.override { nodejs = pkgs."nodejs-6_x"; };

  pkgsUpdates = {
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
      node2nix --flatten --pkg-name nodejs-6_x --development --composition package.nix
      rm -rf elm-stuff
      elm-package install -y
      elm2nix elm-package.nix
      popd
    '';
  };

in pkgs.stdenv.mkDerivation {
  name = "update-relengapi";
  buildInputs = [ elmPackages.elm elm2nix ];  # TODO: add pypi2nix
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
