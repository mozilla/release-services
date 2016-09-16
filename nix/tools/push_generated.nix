# generated using pypi2nix tool (version: 1.5.0.dev0)
#
# COMMAND:
#   pypi2nix --basename push -V 3.5 -r push.txt -v
#

{ pkgs, python, commonBuildInputs ? [], commonDoCheck ? false }:

self: {

  "push" = python.mkDerivation {
    name = "push-0.0.1";
    src = ./../../push;
    #src = pkgs.fetchurl {
    #  url = "https://github.com/garbas/push/archive/ffb8d5c1e9d9b06dd948efb2ddb8d7dbbe7960ca.tar.gz";
    #  sha256 = "b8f17fe25a6adf9aa4d42fd1c6430b0a7649f5e7234298b8630b0a73d007e351";
    #};
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."requests"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = "";
      description = "Utility to push tar.gz docker images to v2 registry";
    };
  };



  "requests" = python.mkDerivation {
    name = "requests-2.11.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/2e/ad/e627446492cc374c284e82381215dcd9a0a87c4f6e90e9789afefe6da0ad/requests-2.11.1.tar.gz";
      sha256 = "5acf980358283faba0b897c73959cecf8b841205bb4b2ad3ef545f46eae1a133";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "Python HTTP for Humans.";
    };
  };

}
