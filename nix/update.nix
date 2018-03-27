let
  requiredNixVersion = "2.0pre";
  pkgs' = import <nixpkgs> {};
  nixpkgs-json = builtins.fromJSON (builtins.readFile ./nixpkgs.json);
  src-nixpkgs = pkgs'.fetchFromGitHub { inherit (nixpkgs-json) owner repo rev sha256; };
  src-nixpkgs-mozilla = pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs-mozilla.json));
in

# ensure we are using correct version of Nix
if ! builtins ? nixVersion || builtins.compareVersions requiredNixVersion builtins.nixVersion >= 0
then abort "mozilla-releng/services requires Nix >= ${requiredNixVersion}, please upgrade."
else

{ pkgs ? import src-nixpkgs {
    overlays = [
      (import "${src-nixpkgs-mozilla}/rust-overlay.nix")
      (import "${src-nixpkgs-mozilla}/firefox-overlay.nix")
    ];
  }
, pkg ? null
}:

let

  releng_pkgs = import ./default.nix { inherit pkgs; };

  packages =
    if pkg == null
      then 
        ((releng_pkgs.lib.packagesWith "update" releng_pkgs.apps) ++
         (releng_pkgs.lib.packagesWith "update" releng_pkgs.tools))
    else if (builtins.substring 0 6 pkg) == "tools."
      then [(builtins.getAttr (builtins.substring 6 (builtins.stringLength pkg) pkg) releng_pkgs.tools)]
    else if (builtins.substring 0 5 pkg) == "apps."
      then [(builtins.getAttr (builtins.substring 5 (builtins.stringLength pkg) pkg) releng_pkgs.apps)]
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
    export LOCALE_ARCHIVE=${pkgs.glibcLocales}/lib/locale/locale-archive
    export LANG=en_US.UTF-8

    echo "Updating packages ..."
    ${builtins.concatStringsSep "\n\n" (
        map (pkg: "echo ' - ${(builtins.parseDrvName pkg.name).name}'; ${if pkg.update == null then "" else pkg.update}") packages)}
    echo "" 
    echo "Packages updated!"
    exit
  '';
}
