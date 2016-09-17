# generated using pypi2nix tool (version: 1.5.0.dev0)
#
# COMMAND:
#   pypi2nix --basename hooks -V 3.5 -r hooks.txt -v
#

{ pkgs, python, commonBuildInputs ? [], commonDoCheck ? false }:

self: {

  "aiohttp" = python.mkDerivation {
    name = "aiohttp-1.0.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/f6/17/3111f78d71208424e2f082e682a25eaf75fd9d737123a37b4799392d783b/aiohttp-1.0.1.tar.gz";
      sha256 = "f5133431d66ef8838f40d233b0fc9e4b9e69616560cbedb89317d551dcc42e41";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."async-timeout"
      self."chardet"
      self."multidict"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "http client/server for asyncio";
    };
  };



  "async-timeout" = python.mkDerivation {
    name = "async-timeout-1.0.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/c3/5b/d00e06296f5fe2c1db230f5f3f39538a4ae23c153adb1672e87e94137f89/async_timeout-1.0.0.tar.gz";
      sha256 = "c7afd7355b93fca0aecc15811aa53eea57f6fd7307b5bff2336b01419ebeda36";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "Timeout context manager for asyncio programs";
    };
  };



  "chardet" = python.mkDerivation {
    name = "chardet-2.3.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/7d/87/4e3a3f38b2f5c578ce44f8dc2aa053217de9f0b6d737739b0ddac38ed237/chardet-2.3.0.tar.gz";
      sha256 = "e53e38b3a4afe6d1132de62b7400a4ac363452dc5dfcf8d88e8e0cce663c68aa";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.lgpl2;
      description = "Universal encoding detector for Python 2 and 3";
    };
  };



  "click" = python.mkDerivation {
    name = "click-6.6";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/7a/00/c14926d8232b36b08218067bcd5853caefb4737cda3f0a47437151344792/click-6.6.tar.gz";
      sha256 = "cc6a19da8ebff6e7074f731447ef7e112bd23adf3de5c597cf9989f2fd8defe9";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "A simple wrapper around optparse for powerful command line utilities.";
    };
  };



  "mohawk" = python.mkDerivation {
    name = "mohawk-0.3.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/6e/c0/fef11cfffdc7729f4dc3dfff70468de0d604c3e2bdcf3170c76b90a7ae1e/mohawk-0.3.3.tar.gz";
      sha256 = "ed68517c20c909abe64bbceb89137b97c1df8c55d95be1c53dfd6c9264003ad0";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."six"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mpl20;
      description = "Library for Hawk HTTP authorization";
    };
  };



  "multidict" = python.mkDerivation {
    name = "multidict-2.0.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/01/a3/f54363a7ba3a7b4660dfa7d07bab2858f2421e341d0ed099ac4346f48586/multidict-2.0.1.tar.gz";
      sha256 = "5f2880534e4e018175ed08a4626e9cb6b5db2c890423bfe24295052cd0ab0bb3";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "multidict implementation";
    };
  };



  "pytest-runner" = python.mkDerivation {
    name = "pytest-runner-2.9";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/11/d4/c335ddf94463e451109e3494e909765c3e5205787b772e3b25ee8601b86a/pytest-runner-2.9.tar.gz";
      sha256 = "50378de59b02f51f64796d3904dfe71b9dc6f06d88fc6bfbd5c8e8366ae1d131";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "Invoke py.test as distutils command with dependency resolution";
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



  "setuptools-scm" = python.mkDerivation {
    name = "setuptools-scm-1.11.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/84/aa/c693b5d41da513fed3f0ee27f1bf02a303caa75bbdfa5c8cc233a1d778c4/setuptools_scm-1.11.1.tar.gz";
      sha256 = "8c45f738a23410c5276b0ed9294af607f491e4260589f1eb90df8312e23819bf";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "the blessed package to manage your versions by scm tags";
    };
  };



  "six" = python.mkDerivation {
    name = "six-1.10.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/b3/b2/238e2590826bfdd113244a40d9d3eb26918bd798fc187e2360a8367068db/six-1.10.0.tar.gz";
      sha256 = "105f8d68616f8248e24bf0e9372ef04d3cc10104f1980f54d57b2ce73a5ad56a";
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



  "slugid" = python.mkDerivation {
    name = "slugid-1.0.7";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/dd/96/b05c6d357f8d6932bea2b360537360517d1154b82cc71b8eccb70b28bdde/slugid-1.0.7.tar.gz";
      sha256 = "6dab3c7eef0bb423fb54cb7752e0f466ddd0ee495b78b763be60e8a27f69e779";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mpl20;
      description = "Base64 encoded uuid v4 slugs";
    };
  };



  "taskcluster" = python.mkDerivation {
    name = "taskcluster-0.3.4";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/3e/50/bb7659d5cf396f5c78013bb35ac92931c852b0ae3fa738bbd9224b6192ef/taskcluster-0.3.4.tar.gz";
      sha256 = "d4fe5e2a44fe27e195b92830ece0a6eb9eb7ad9dc556a0cb16f6f2a6429f1b65";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."aiohttp"
      self."mohawk"
      self."requests"
      self."six"
      self."slugid"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = "";
      description = "Python client for Taskcluster";
    };
  };

}