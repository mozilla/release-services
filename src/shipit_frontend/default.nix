{ releng_pkgs
}:
let
  inherit (builtins) readFile;
  inherit (releng_pkgs.lib) mkFrontend;
  inherit (releng_pkgs.pkgs.lib) fileContents;
in mkFrontend {
  name = "shipit_frontend";
  version = fileContents ./../../VERSION;
  csp = "default-src 'none'; img-src 'self' data: *.gravatar.com; script-src 'self'; style-src 'self'; font-src 'self';";
  src = ./.;
  node_modules = import ./node-modules.nix { inherit (releng_pkgs) pkgs; };
  elm_packages = import ./elm-packages.nix;
  production = true;
}
