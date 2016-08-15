# generated using pypi2nix tool (version: 1.4.0.dev0)
#
# COMMAND:
#   pypi2nix -v -V 3.5 -r requirements.txt
#

{ pkgs, python, commonBuildInputs ? [], commonDoCheck ? false }:

self: {

  "Pygments" = python.mkDerivation {
    name = "Pygments-2.1.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/b8/67/ab177979be1c81bc99c8d0592ef22d547e70bb4c6815c383286ed5dec504/Pygments-2.1.3.tar.gz";
      sha256= "88e4c8a91b2af5962bfa5ea2447ec6dd357018e86e94c7d14bd8cacbc5b55d81";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Pygments is a syntax highlighting package written in Python.";
    };
  };



  "aws-shell" = python.mkDerivation {
    name = "aws-shell-0.1.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/3f/d1/0f5bdb9833f2a57095bc133fa603de8e8931f6ca44653bd56afda8148e0f/aws-shell-0.1.1.tar.gz";
      sha256= "653f085d966b4ed3b3581b7bb85f6f0bb1e8a3bfd852a3333596082a5ba689df";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Pygments"
      self."awscli"
      self."boto3"
      self."configobj"
      self."prompt-toolkit"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "AWS Shell";
    };
  };



  "awscli" = python.mkDerivation {
    name = "awscli-1.10.56";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/8b/38/c3cb424d6117c1f096496ba6f26dd05635b6c5660ee4acef00369641f007/awscli-1.10.56.tar.gz";
      sha256= "adbc8812e75f0be53c4a414aeb181be6838befcd2869427074e116cf0cc6f7a2";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."botocore"
      self."colorama"
      self."docutils"
      self."rsa"
      self."s3transfer"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "Universal Command Line Environment for AWS.";
    };
  };



  "boto3" = python.mkDerivation {
    name = "boto3-1.4.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/37/1a/e271b2937c05c1da265415103725e0610fb96871a2d7ddf68b999ac5db8f/boto3-1.4.0.tar.gz";
      sha256= "c365144fb98d022ad6f6cdeb1abf8a4849f1a135e3c4ef78ef5053982ed914b3";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."botocore"
      self."jmespath"
      self."s3transfer"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "The AWS SDK for Python";
    };
  };



  "botocore" = python.mkDerivation {
    name = "botocore-1.4.46";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/df/2b/c0dec83c2bccb9d0f1c3cc33dc4bd0752b76a2e4d30fb46061063cf3d7ea/botocore-1.4.46.tar.gz";
      sha256= "844dbd090b4127678c25342635485c87d86bca4a4f8a7c2295d715f7c830700c";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."docutils"
      self."jmespath"
      self."python-dateutil"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "Low-level, data-driven core of boto 3.";
    };
  };



  "colorama" = python.mkDerivation {
    name = "colorama-0.3.7";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/f0/d0/21c6449df0ca9da74859edc40208b3a57df9aca7323118c913e58d442030/colorama-0.3.7.tar.gz";
      sha256= "e043c8d32527607223652021ff648fbb394d5e19cba9f1a698670b338c9d782b";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Cross-platform colored terminal text.";
    };
  };



  "configobj" = python.mkDerivation {
    name = "configobj-5.0.6";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/64/61/079eb60459c44929e684fa7d9e2fdca403f67d64dd9dbac27296be2e0fab/configobj-5.0.6.tar.gz";
      sha256= "a2f5650770e1c87fb335af19a9b7eb73fc05ccf22144eb68db7d00cd2bcb0902";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."six"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Config file reading, writing and validation.";
    };
  };



  "docutils" = python.mkDerivation {
    name = "docutils-0.12";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/37/38/ceda70135b9144d84884ae2fc5886c6baac4edea39550f28bcd144c1234d/docutils-0.12.tar.gz";
      sha256= "c7db717810ab6965f66c8cf0398a98c9d8df982da39b4cd7f162911eb89596fa";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.publicDomain;
      description = "Docutils -- Python Documentation Utilities";
    };
  };



  "jmespath" = python.mkDerivation {
    name = "jmespath-0.9.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/8f/d8/6e3e602a3e90c5e3961d3d159540df6b2ff32f5ab2ee8ee1d28235a425c1/jmespath-0.9.0.tar.gz";
      sha256= "08dfaa06d4397f283a01e57089f3360e3b52b5b9da91a70e1fd91e9f0cdd3d3d";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "JSON Matching Expressions";
    };
  };



  "prompt-toolkit" = python.mkDerivation {
    name = "prompt-toolkit-1.0.5";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/c0/d0/dcb9235c812b70f20d8d1ff110f9caa85daf4bf1ec2ac10516f51c07957e/prompt_toolkit-1.0.5.tar.gz";
      sha256= "b726807349e8158a70773cf6ac2a90f0c62849dd02a339aac910ba1cd882f313";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."six"
      self."wcwidth"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Library for building powerful interactive command lines in Python";
    };
  };



  "pyasn1" = python.mkDerivation {
    name = "pyasn1-0.1.9";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/f7/83/377e3dd2e95f9020dbd0dfd3c47aaa7deebe3c68d3857a4e51917146ae8b/pyasn1-0.1.9.tar.gz";
      sha256= "853cacd96d1f701ddd67aa03ecc05f51890135b7262e922710112f12a2ed2a7f";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "ASN.1 types and codecs";
    };
  };



  "python-dateutil" = python.mkDerivation {
    name = "python-dateutil-2.5.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/3e/f5/aad82824b369332a676a90a8c0d1e608b17e740bbb6aeeebca726f17b902/python-dateutil-2.5.3.tar.gz";
      sha256= "1408fdb07c6a1fa9997567ce3fcee6a337b39a503d80699e0f213de4aa4b32ed";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."six"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Extensions to the standard Python datetime module";
    };
  };



  "rsa" = python.mkDerivation {
    name = "rsa-3.4.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/14/89/adf8b72371e37f3ca69c6cb8ab6319d009c4a24b04a31399e5bd77d9bb57/rsa-3.4.2.tar.gz";
      sha256= "25df4e10c263fb88b5ace923dd84bf9aa7f5019687b5e55382ffcdb8bede9db5";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."pyasn1"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = "License :: OSI Approved :: Apache Software License";
      description = "Pure-Python RSA implementation";
    };
  };



  "s3transfer" = python.mkDerivation {
    name = "s3transfer-0.1.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/27/58/c3c67734ac87ef83fdffb6e1167531d584111232ad5e13b5514831a5de35/s3transfer-0.1.1.tar.gz";
      sha256= "6b9131b704819b0e559a97eec373ff6cc8a9b258e4c8f58ad339650b5019f00f";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."botocore"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "An Amazon S3 Transfer Manager";
    };
  };



  "six" = python.mkDerivation {
    name = "six-1.10.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/b3/b2/238e2590826bfdd113244a40d9d3eb26918bd798fc187e2360a8367068db/six-1.10.0.tar.gz";
      sha256= "105f8d68616f8248e24bf0e9372ef04d3cc10104f1980f54d57b2ce73a5ad56a";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "Python 2 and 3 compatibility utilities";
    };
  };



  "wcwidth" = python.mkDerivation {
    name = "wcwidth-0.1.7";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/55/11/e4a2bb08bb450fdbd42cc709dd40de4ed2c472cf0ccb9e64af22279c5495/wcwidth-0.1.7.tar.gz";
      sha256= "3df37372226d6e63e1b1e1eda15c594bca98a22d33a23832a90998faa96bc65e";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "Measures number of Terminal column cells of wide-character codes";
    };
  };

}