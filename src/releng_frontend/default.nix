{ releng_pkgs
}:
let
  inherit (builtins) readFile;
  inherit (releng_pkgs.lib) mkFrontend;
  inherit (releng_pkgs.pkgs.lib) fileContents;

  nodejs = releng_pkgs.pkgs."nodejs-6_x";
  node_modules = import ./node-modules.nix {
    inherit nodejs;
    inherit (releng_pkgs) pkgs;
  };
  elm_packages = import ./elm-packages.nix;

in mkFrontend {
  inProduction = true;
  project_name = "releng-frontend";
  inherit nodejs node_modules elm_packages;
  version = fileContents ./VERSION;
  src = ./.;
  src_path = "src/releng_frontend";
  postInstall = ''
    cp -R src/static/* $out/
  '';
}
