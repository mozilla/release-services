{ releng_pkgs
}:
let
  inherit (builtins) readFile;
  inherit (releng_pkgs.lib) mkFrontend;
  inherit (releng_pkgs.pkgs.lib) fileContents;
in mkFrontend {
  name = "releng_frontend";
  version = fileContents ./../../VERSION;
  src = ./.;
  node_modules = import ./node-modules.nix { inherit (releng_pkgs) pkgs; };
  elm_packages = import ./elm-packages.nix;
  postInstall = ''
    mkdir -p $out/trychooser
    cp src/trychooser/* $out/trychooser/
  '';
}
