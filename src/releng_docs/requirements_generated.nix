# generated using pypi2nix tool (version: 1.6.0)
#
# COMMAND:
#   pypi2nix -v -V 3.5 -r requirements.txt
#

{ pkgs, python, commonBuildInputs ? [], commonDoCheck ? false }:

self: {

  "Babel" = python.mkDerivation {
    name = "Babel-2.3.4";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/6e/96/ba2a2462ed25ca0e651fb7b66e7080f5315f91425a07ea5b34d7c870c114/Babel-2.3.4.tar.gz";
      sha256 = "c535c4403802f6eb38173cd4863e419e2274921a01a8aad8a5b497c131c62875";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."pytz"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Internationalization utilities";
    };
  };



  "Jinja2" = python.mkDerivation {
    name = "Jinja2-2.8";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/f2/2f/0b98b06a345a761bec91a079ccae392d282690c2d8272e708f4d10829e22/Jinja2-2.8.tar.gz";
      sha256 = "bc1ff2ff88dbfacefde4ddde471d1417d3b304e8df103a7a9437d47269201bf4";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Babel"
      self."MarkupSafe"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "A small but fast and easy to use stand-alone template engine written in pure python.";
    };
  };



  "MarkupSafe" = python.mkDerivation {
    name = "MarkupSafe-0.23";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/c0/41/bae1254e0396c0cc8cf1751cb7d9afc90a602353695af5952530482c963f/MarkupSafe-0.23.tar.gz";
      sha256 = "a4ec1aff59b95a14b45eb2e23761a0179e98319da5a7eb76b56ea8cdc7b871c3";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Implements a XML/HTML/XHTML Markup safe string for Python";
    };
  };



  "Pygments" = python.mkDerivation {
    name = "Pygments-2.1.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/b8/67/ab177979be1c81bc99c8d0592ef22d547e70bb4c6815c383286ed5dec504/Pygments-2.1.3.tar.gz";
      sha256 = "88e4c8a91b2af5962bfa5ea2447ec6dd357018e86e94c7d14bd8cacbc5b55d81";
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



  "Sphinx" = python.mkDerivation {
    name = "Sphinx-1.4.9";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/c5/21/ccd4567e5918e7fd61bce03421ae6ff6912b84e11728c1fd02a1cf85c17d/Sphinx-1.4.9.tar.gz";
      sha256 = "82cd2728c906be96e307b81352d3fd9fb731869234c6b835cc25e9a3dfb4b7e4";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Babel"
      self."Jinja2"
      self."Pygments"
      self."alabaster"
      self."docutils"
      self."imagesize"
      self."six"
      self."snowballstemmer"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Python documentation generator";
    };
  };



  "alabaster" = python.mkDerivation {
    name = "alabaster-0.7.9";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/71/c3/70da7d8ac18a4f4c502887bd2549e05745fa403e2cd9d06a8a9910a762bc/alabaster-0.7.9.tar.gz";
      sha256 = "47afd43b08a4ecaa45e3496e139a193ce364571e7e10c6a87ca1a4c57eb7ea08";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "A configurable sidebar-enabled Sphinx theme";
    };
  };



  "docutils" = python.mkDerivation {
    name = "docutils-0.12";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/37/38/ceda70135b9144d84884ae2fc5886c6baac4edea39550f28bcd144c1234d/docutils-0.12.tar.gz";
      sha256 = "c7db717810ab6965f66c8cf0398a98c9d8df982da39b4cd7f162911eb89596fa";
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



  "imagesize" = python.mkDerivation {
    name = "imagesize-0.7.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/53/72/6c6f1e787d9cab2cc733cf042f125abec07209a58308831c9f292504e826/imagesize-0.7.1.tar.gz";
      sha256 = "0ab2c62b87987e3252f89d30b7cedbec12a01af9274af9ffa48108f2c13c6062";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "Getting image size from png/jpeg/jpeg2000/gif file";
    };
  };



  "livereload" = python.mkDerivation {
    name = "livereload-2.5.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/ba/71/2660028c74cb3289d4b9fd06632aa277b4edbe0747b7219cd92307fa19ba/livereload-2.5.0.tar.gz";
      sha256 = "bc708b46e22dff243c02e709c636ffeb8a64cdd019c95a215304e6ce183c4859";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."six"
      self."tornado"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Python LiveReload is an awesome tool for web developers";
    };
  };



  "pytz" = python.mkDerivation {
    name = "pytz-2016.7";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/53/35/6376f58fb82ce69e2c113ca0ebe5c0f69b20f006e184bcc238a6007f4bdb/pytz-2016.7.tar.bz2";
      sha256 = "6eab31709e3a4aea748457707da45e805b650cbb352583805d2417de2a1dd71e";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "World timezone definitions, modern and historical";
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



  "snowballstemmer" = python.mkDerivation {
    name = "snowballstemmer-1.2.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/20/6b/d2a7cb176d4d664d94a6debf52cd8dbae1f7203c8e42426daa077051d59c/snowballstemmer-1.2.1.tar.gz";
      sha256 = "919f26a68b2c17a7634da993d91339e288964f93c274f1343e3bbbe2096e1128";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "This package provides 16 stemmer algorithms (15 + Poerter English stemmer) generated from Snowball algorithms.";
    };
  };



  "tornado" = python.mkDerivation {
    name = "tornado-4.4.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/1e/7c/ea047f7bbd1ff22a7f69fe55e7561040e3e54d6f31da6267ef9748321f98/tornado-4.4.2.tar.gz";
      sha256 = "2898f992f898cd41eeb8d53b6df75495f2f423b6672890aadaf196ea1448edcc";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = "License :: OSI Approved :: Apache Software License";
      description = "Tornado is a Python web framework and asynchronous networking library, originally developed at FriendFeed.";
    };
  };

}