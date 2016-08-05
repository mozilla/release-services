# generated using pypi2nix tool (version: 1.4.0.dev0)
# See more at: https://github.com/garbas/pypi2nix
#
# COMMAND:
#   pypi2nix -V 3.5 -r requirements.txt -r requirements-prod.txt -r requirements-dev.txt -E postgresql
#

{ pkgs ? import <nixpkgs> {}
}:

let

  inherit (pkgs.stdenv.lib) fix' extends inNixShell;

  pythonPackages = import <nixpkgs/pkgs/top-level/python-packages.nix> {
    inherit pkgs;
    inherit (pkgs) stdenv;
    python = pkgs.python35;
    self = pythonPackages;
  };

  commonBuildInputs = with pkgs; [ postgresql ];
  commonDoCheck = false;

  buildEnv = { pkgs ? {} }:
    let
      interpreter = pythonPackages.python.buildEnv.override {
        extraLibs = builtins.attrValues pkgs;
      };
    in {
      mkDerivation = pythonPackages.buildPythonPackage;
      interpreter = if inNixShell then interpreter.env else interpreter;
      overrideDerivation = drv: f: pythonPackages.buildPythonPackage (drv.drvAttrs // f drv.drvAttrs);
      withPackages = pkgs': buildEnv { pkgs = pkgs'; };
      inherit buildEnv pkgs;
      __old = pythonPackages;
    };

  python = buildEnv {};
  generated = import ./requirements_generated.nix { inherit pkgs python commonBuildInputs commonDoCheck; };
  overrides = import ./requirements_override.nix { inherit pkgs python; };

  python' = buildEnv {
    pkgs = builtins.removeAttrs (fix' (extends overrides generated)) ["__unfix__"];

  };

in python'