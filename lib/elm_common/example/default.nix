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

in mkFrontend {
  inherit nodejs node_modules;
  name = "elm_common_example";
  version = fileContents ./../../../VERSION;
  src = ./.;
  src_path = "lib/elm_common/example";
  elm_packages = import ./elm-packages.nix;
}
#    "build": "rimraf dist && webpack && mv dist/*.eot dist/static/css/ && mv dist/*.woff* dist/static/css/ && mv dist/*.svg dist/static/css/ && mv dist/*.ttf dist/static/css/"
