let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json))) {}
, pkg ? null
}:

let

  releng_pkgs = import ./default.nix { inherit pkgs; };

  packages =
    if pkg == null
      then 
        ((releng_pkgs.lib.packagesWith "update" releng_pkgs) ++
         (releng_pkgs.lib.packagesWith "update" releng_pkgs.tools))
    else if (builtins.substring 0 6 pkg) == "tools."
      then [(builtins.getAttr (builtins.substring 6 100 pkg) releng_pkgs.tools)]
    else
      [(builtins.getAttr pkg releng_pkgs)];

in pkgs.stdenv.mkDerivation {
  name = "update-releng";
  buildCommand = ''
    echo "+--------------------------------------------------------+"
    echo "| Not possible to update repositories using \`nix-build\`. |"
    echo "|         Please run \`nix-shell update.nix\`.             |"
    echo "+--------------------------------------------------------+"
    exit 1
  '';
  shellHook = ''
    export HOME=$PWD
    export NIX_PATH=nixpkgs=${pkgs.path}
    echo "Updating packages ..."
    ${builtins.concatStringsSep "\n\n" (
        map (pkg: "echo ' - ${(builtins.parseDrvName pkg.name).name}'; ${if pkg.update == null then "" else pkg.update}") packages)}
    echo "" 
    echo "Packages updated!"
    exit
  '';
}
