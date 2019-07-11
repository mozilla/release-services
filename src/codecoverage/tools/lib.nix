{ pkgs ? import <nixpkgs> {},
  overrides ? ({ pkgs, python }: self: super: {})
}:

let 
  pythonPackages =
    import "${toString pkgs.path}/pkgs/top-level/python-packages.nix" {
      inherit pkgs;
      inherit (pkgs) stdenv;
      python = pkgs.python37;
    };

in pythonPackages.buildPythonPackage rec {
  name = "code-coverage-tools";
  version = "0.1.0";

  src = ./.;

  doCheck = false;

  meta = with pkgs.stdenv.lib; {
    homepage = https://github.com/mozilla/release-services;
    description = "Mozilla code coverage lib";
    license = licenses.mpl20;
  };
}
