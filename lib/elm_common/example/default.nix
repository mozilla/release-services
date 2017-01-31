{ releng_pkgs
}:
let
  inherit (builtins) readFile;
  inherit (releng_pkgs.lib) mkFrontend;
  inherit (releng_pkgs.pkgs.lib) fileContents;
in mkFrontend {
  name = "elm_common_example";
  version = fileContents ./../../../VERSION;
  src = ./.;
  src_path = "lib/elm_common/example";
  node_modules = import ./node-modules.nix { inherit (releng_pkgs) pkgs; };
  elm_packages = import ./elm-packages.nix;
}
