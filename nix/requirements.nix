# generated using pypi2nix tool (version: 1.4.0.dev0)
# See more at: https://github.com/garbas/pypi2nix
#
# COMMAND:
#   pypi2nix -v -V 3.5 -r requirements.txt
#

{ pkgs ? import <nixpkgs> {}
}:

let

  inherit (pkgs.stdenv.lib) fix' extends inNixShell;

  pythonPackages = import "${toString pkgs.path}/pkgs/top-level/python-packages.nix" {
    inherit pkgs;
    inherit (pkgs) stdenv;
    python = pkgs.python35;
    self = pythonPackages;
  };

  commonBuildInputs = with pkgs; [ postgresql ];
  commonDoCheck = false;

  withPackages = pkgs:
    let
      pkgs' = builtins.removeAttrs pkgs ["__unfix__"];
    in {
      __old = pythonPackages;
      interpreter = pythonPackages.python;  # TODO: we should wrap python with PYTHONPATH and forward passthru
      mkDerivation = pythonPackages.buildPythonPackage;
      packages = pkgs';
      overrideDerivation = drv: f:
        pythonPackages.buildPythonPackage (drv.drvAttrs // f drv.drvAttrs);
      withPackages = pkgs:
        withPackages (pkgs' // pkgs);
    };

  python = withPackages {};

  generated = import ./requirements_generated.nix { inherit pkgs python commonBuildInputs commonDoCheck; };
  overrides = import ./requirements_override.nix { inherit pkgs python; };

in python.withPackages (fix' (extends overrides generated))
