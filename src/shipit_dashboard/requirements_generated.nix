# generated using pypi2nix tool (version: 1.6.0)
#
# COMMAND:
#   pypi2nix -v -V 3.5 -E postgresql -s six packaging appdirs -r ../../lib/releng_common/requirements-dev.txt -r requirements.txt -r requirements-dev.txt -r requirements-nix.txt
#

{ pkgs, python, commonBuildInputs ? [], commonDoCheck ? false }:

self: {

  "Flask" = python.mkDerivation {
    name = "Flask-0.12";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/4b/3a/4c20183df155dd2e39168e35d53a388efb384a512ca6c73001d8292c094a/Flask-0.12.tar.gz";
      sha256 = "93e803cdbe326a61ebd5c5d353959397c85f829bec610d59cb635c9f97d7ca8b";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Jinja2"
      self."Werkzeug"
      self."click"
      self."itsdangerous"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "A microframework based on Werkzeug, Jinja2 and good intentions";
    };
  };



  "Flask-Cors" = python.mkDerivation {
    name = "Flask-Cors-3.0.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/1d/ea/86765a4ae667b4517dc16ef0fc8dd632ca3ea56ef419c4a6de31e715324e/Flask-Cors-3.0.2.tar.gz";
      sha256 = "0a09f3559ded4759387dfa2a355de59bc161f67269a1f4b7b0712a64b1f7dad6";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Flask"
      self."six"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "A Flask extension adding a decorator for CORS support";
    };
  };



  "Flask-Login" = python.mkDerivation {
    name = "Flask-Login-0.4.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/70/96/20cae731ef27084dcb183f3a6e3073d0232f10c1fd7be76729bd7bd4b994/Flask-Login-0.4.0.tar.gz";
      sha256 = "d25e356b14a59f52da0ab30c31c2ad285fa23a840f0f6971df7ed247c77082a7";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Flask"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "User session management for Flask";
    };
  };



  "Flask-Migrate" = python.mkDerivation {
    name = "Flask-Migrate-2.0.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/f8/ba/827214fb932fb1de1fac7d992f0958c799bfc50ea471b0b8792d5e72daa6/Flask-Migrate-2.0.2.tar.gz";
      sha256 = "c77272b936ec94209d5c709f9ec43947f4a25513c1b12cc25241586abdfa84b1";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Flask"
      self."Flask-SQLAlchemy"
      self."Flask-Script"
      self."alembic"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "SQLAlchemy database migrations for Flask applications using Alembic";
    };
  };



  "Flask-SQLAlchemy" = python.mkDerivation {
    name = "Flask-SQLAlchemy-2.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/b3/52/227aaf4e8cebb153e239c518a9e916590b2fe0e4350e6b02d92b546b69b7/Flask-SQLAlchemy-2.1.tar.gz";
      sha256 = "c5244de44cc85d2267115624d83faef3f9e8f088756788694f305a5d5ad137c5";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Flask"
      self."SQLAlchemy"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Adds SQLAlchemy support to your Flask application";
    };
  };



  "Flask-Script" = python.mkDerivation {
    name = "Flask-Script-2.0.5";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/66/e9/2b3c7c548a6bad0b59da21e2050613da43aae4da617fb98847efa3e09a43/Flask-Script-2.0.5.tar.gz";
      sha256 = "cef76eac751396355429a14c38967bb14d4973c53e07dec94af5cc8fb017107f";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Flask"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Scripting support for Flask";
    };
  };



  "Jinja2" = python.mkDerivation {
    name = "Jinja2-2.9.4";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/f4/3f/28387a5bbc6883082c16784c6135440b94f9d5938fb156ff579798e18eda/Jinja2-2.9.4.tar.gz";
      sha256 = "aab8d8ca9f45624f1e77f2844bf3c144d180e97da8824c2a6d7552ad039b5442";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."MarkupSafe"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "A small but fast and easy to use stand-alone template engine written in pure python.";
    };
  };



  "Logbook" = python.mkDerivation {
    name = "Logbook-1.0.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/34/e8/6419c217bbf464fe8a902418120cccaf476201bd03b50958db24d6e90f65/Logbook-1.0.0.tar.gz";
      sha256 = "87da2515a6b3db866283cb9d4e5a6ec44e52a1d556ebb2ea3b6e7e704b5f1872";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Jinja2"
      self."SQLAlchemy"
      self."pytest"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "A logging replacement for Python";
    };
  };



  "Mako" = python.mkDerivation {
    name = "Mako-1.0.6";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/56/4b/cb75836863a6382199aefb3d3809937e21fa4cb0db15a4f4ba0ecc2e7e8e/Mako-1.0.6.tar.gz";
      sha256 = "48559ebd872a8e77f92005884b3d88ffae552812cdf17db6768e5c3be5ebbe0d";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."MarkupSafe"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "A super-fast templating language that borrows the  best ideas from the existing templating languages.";
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



  "PyYAML" = python.mkDerivation {
    name = "PyYAML-3.12";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/4a/85/db5a2df477072b2902b0eb892feb37d88ac635d36245a72a6a69b23b383a/PyYAML-3.12.tar.gz";
      sha256 = "592766c6303207a20efc445587778322d7f73b161bd994f227adaa341ba212ab";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "YAML parser and emitter for Python";
    };
  };



  "Pygments" = python.mkDerivation {
    name = "Pygments-2.2.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/71/2a/2e4e77803a8bd6408a2903340ac498cb0a2181811af7c9ec92cb70b0308a/Pygments-2.2.0.tar.gz";
      sha256 = "dbae1046def0efb574852fab9e90209b23f556367b5a320c0bcb871c77c3e8cc";
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



  "SQLAlchemy" = python.mkDerivation {
    name = "SQLAlchemy-1.1.5";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/da/04/8048a5075d6e29235bbd6f1ea092a38dbe2630c670e73d4aa923a4e5521c/SQLAlchemy-1.1.5.tar.gz";
      sha256 = "68fb40049690e567ebda7b270176f5abf0d53d9fbd515fec4e43326f601119b6";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."psycopg2"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "Database Abstraction Library";
    };
  };



  "Werkzeug" = python.mkDerivation {
    name = "Werkzeug-0.11.15";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/fe/7f/6d70f765ce5484e07576313897793cb49333dd34e462488ee818d17244af/Werkzeug-0.11.15.tar.gz";
      sha256 = "455d7798ac263266dbd38d4841f7534dd35ca9c3da4a8df303f8488f38f3bcc0";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "The Swiss Army knife of Python web development";
    };
  };



  "aiohttp" = python.mkDerivation {
    name = "aiohttp-1.2.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/e5/a5/ade96691f6423c56f7911a42a51ecd5454619efd6d5026df7e08a556a36a/aiohttp-1.2.0.tar.gz";
      sha256 = "8ce0ab4301bf38db2ae13e4921bdb3841507919c9121373405a43c7bd0a07f78";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."async-timeout"
      self."chardet"
      self."multidict"
      self."yarl"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "http client/server for asyncio";
    };
  };



  "alembic" = python.mkDerivation {
    name = "alembic-0.8.10";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/f0/7d/7fcda63887d9726e0145e98802baf374ec8cf889325e469194cd7926c98e/alembic-0.8.10.tar.gz";
      sha256 = "0e3b50e96218283ec7443fb661199f5a81f5879f766967a8a2d25e8f9d4e7919";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Mako"
      self."SQLAlchemy"
      self."python-editor"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "A database migration tool for SQLAlchemy.";
    };
  };



  "appdirs" = python.mkDerivation {
    name = "appdirs-1.4.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/bd/66/0a7f48a0f3fb1d3a4072bceb5bbd78b1a6de4d801fb7135578e7c7b1f563/appdirs-1.4.0.tar.gz";
      sha256 = "8fc245efb4387a4e3e0ac8ebcc704582df7d72ff6a42a53f5600bbb18fdaadc5";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "A small Python module for determining appropriate \" +         \"platform-specific dirs, e.g. a \"user data dir\".";
    };
  };



  "async-timeout" = python.mkDerivation {
    name = "async-timeout-1.1.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/29/f6/eeac39dfadd3a7610bb33842cf611a1f09fcd2e445ab76e4c951efde0c2b/async-timeout-1.1.0.tar.gz";
      sha256 = "b88bd1fe001b800ec23c7bf27a81b32819e2a56668e9fba5646a7f3618143081";
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
    name = "click-6.7";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/95/d9/c3336b6b5711c3ab9d1d3a80f1a3e2afeb9d8c02a7166462f6cc96570897/click-6.7.tar.gz";
      sha256 = "f15516df478d5a56180fbf80e68f206010e6d160fc39fa508b65e035fd75130b";
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



  "clickclick" = python.mkDerivation {
    name = "clickclick-1.2.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/6f/46/28462eb039bbce3651084d5260c50ab83dc3af0724626e6a81c93d950b2c/clickclick-1.2.1.tar.gz";
      sha256 = "22eedfce2499d7a8c5b8c868fc93a495eb74bf7b753a6cb9ed2aa6a32a3ddd05";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."PyYAML"
      self."click"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "Click utility functions";
    };
  };



  "connexion" = python.mkDerivation {
    name = "connexion-1.0.129";
    src = pkgs.fetchurl { url = "https://pypi.python.org/packages/ca/b1/1b40f5ba85b275bfc1878d030722809281e4a6f05c62b75abba3861be9f7/connexion-1.0.129.tar.gz"; sha256 = "dbee8e66c66c09e0db3083bd40f6c2c1a6ae193e06bb57c48202642429da70ad"; };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Flask"
      self."PyYAML"
      self."clickclick"
      self."jsonschema"
      self."requests"
      self."six"
      self."strict-rfc3339"
      self."swagger-spec-validator"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "Connexion - API first applications with OpenAPI/Swagger and Flask";
    };
  };



  "cookies" = python.mkDerivation {
    name = "cookies-2.2.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/f3/95/b66a0ca09c5ec9509d8729e0510e4b078d2451c5e33f47bd6fc33c01517c/cookies-2.2.1.tar.gz";
      sha256 = "d6b698788cae4cfa4e62ef8643a9ca332b79bd96cb314294b864ae8d7eb3ee8e";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "Friendlier RFC 6265-compliant cookie parser/renderer";
    };
  };



  "decorator" = python.mkDerivation {
    name = "decorator-4.0.11";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/cc/ac/5a16f1fc0506ff72fcc8fd4e858e3a1c231f224ab79bb7c4c9b2094cc570/decorator-4.0.11.tar.gz";
      sha256 = "953d6bf082b100f43229cf547f4f97f97e970f5ad645ee7601d55ff87afdfe76";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Better living through Python with decorators";
    };
  };



  "flake8" = python.mkDerivation {
    name = "flake8-3.2.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/51/70/af1b3130cd051f2f79854b14079b3bcbad84b8bac31a7dffc63ef57f8a7a/flake8-3.2.1.tar.gz";
      sha256 = "c7c460b5aff3a2063c798a77af18ec70af3941d35a22e2e76965e3c0e0b36055";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."mccabe"
      self."pycodestyle"
      self."pyflakes"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "the modular source code checker: pep8, pyflakes and co";
    };
  };



  "gunicorn" = python.mkDerivation {
    name = "gunicorn-19.6.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/84/ce/7ea5396efad1cef682bbc4068e72a0276341d9d9d0f501da609fab9fcb80/gunicorn-19.6.0.tar.gz";
      sha256 = "813f6916d18a4c8e90efde72f419308b357692f81333cb1125f80013d22fb618";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "WSGI HTTP Server for UNIX";
    };
  };



  "ipdb" = python.mkDerivation {
    name = "ipdb-0.10.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/e1/fa/446cc6443c0dd5bcce55af12b73e1a561b330913a3792d4037f4aa654ed2/ipdb-0.10.2.tar.gz";
      sha256 = "fffc45b615e46eb75becbd88a30c69c75e7164ecd0122f2c78579b4dfa41b8c9";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."ipython"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "IPython-enabled pdb";
    };
  };



  "ipython" = python.mkDerivation {
    name = "ipython-5.1.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/89/63/a9292f7cd9d0090a0f995e1167f3f17d5889dcbc9a175261719c513b9848/ipython-5.1.0.tar.gz";
      sha256 = "7ef4694e1345913182126b219aaa4a0047e191af414256da6772cf249571b961";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Pygments"
      self."decorator"
      self."pexpect"
      self."pickleshare"
      self."prompt-toolkit"
      self."requests"
      self."simplegeneric"
      self."traitlets"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "IPython: Productive Interactive Computing";
    };
  };



  "ipython-genutils" = python.mkDerivation {
    name = "ipython-genutils-0.1.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/71/b7/a64c71578521606edbbce15151358598f3dfb72a3431763edc2baf19e71f/ipython_genutils-0.1.0.tar.gz";
      sha256 = "3a0624a251a26463c9dfa0ffa635ec51c4265380980d9a50d65611c3c2bd82a6";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Vestigial utilities from IPython";
    };
  };



  "itsdangerous" = python.mkDerivation {
    name = "itsdangerous-0.24";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/dc/b4/a60bcdba945c00f6d608d8975131ab3f25b22f2bcfe1dab221165194b2d4/itsdangerous-0.24.tar.gz";
      sha256 = "cbb3fcf8d3e33df861709ecaf89d9e6629cff0a217bc2848f1b41cd30d360519";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Various helpers to pass trusted data to untrusted environments and back.";
    };
  };



  "jsonschema" = python.mkDerivation {
    name = "jsonschema-2.5.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/58/0d/c816f5ea5adaf1293a1d81d32e4cdfdaf8496973aa5049786d7fdb14e7e7/jsonschema-2.5.1.tar.gz";
      sha256 = "36673ac378feed3daa5956276a829699056523d7961027911f064b52255ead41";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."strict-rfc3339"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "An implementation of JSON Schema validation for Python";
    };
  };



  "mccabe" = python.mkDerivation {
    name = "mccabe-0.5.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/c9/0b/b66016d49fc1b24864743e388bc4fa7dcbb83c29553b867404fad5b5855d/mccabe-0.5.3.tar.gz";
      sha256 = "16293af41e7242031afd73896fef6458f4cad38201d21e28f344fff50ae1c25e";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "McCabe checker, plugin for flake8";
    };
  };



  "mohawk" = python.mkDerivation {
    name = "mohawk-0.3.4";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/19/22/10f696548a8d41ad41b92ab6c848c60c669e18c8681c179265ce4d048b03/mohawk-0.3.4.tar.gz";
      sha256 = "e98b331d9fa9ece7b8be26094cbe2d57613ae882133cc755167268a984bc0ab3";
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
    name = "multidict-2.1.4";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/2a/df/eaea73e46a58fd780c35ecc304ca42364fa3c1f4cd03568ed33b9d2c7547/multidict-2.1.4.tar.gz";
      sha256 = "a77aa8c9f68846c3b5db43ff8ed2a7a884dbe845d01f55113a3fba78518c4cd7";
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



  "newrelic" = python.mkDerivation {
    name = "newrelic-2.78.0.57";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/fa/58/ec86f921560cb2fda82c0ee5db5565481978b665998bb32b9c8b077017c0/newrelic-2.78.0.57.tar.gz";
      sha256 = "2191b7699e14a07efa5d9221270eb29bdf6cce643aa56cff08546ecb3f729be6";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = "License :: Other/Proprietary License";
      description = "New Relic Python Agent";
    };
  };



  "packaging" = python.mkDerivation {
    name = "packaging-16.8";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/c6/70/bb32913de251017e266c5114d0a645f262fb10ebc9bf6de894966d124e35/packaging-16.8.tar.gz";
      sha256 = "5d50835fdf0a7edf0b55e311b7c887786504efea1177abd7e69329a8e5ea619e";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."pyparsing"
      self."six"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Core utilities for Python packages";
    };
  };



  "pexpect" = python.mkDerivation {
    name = "pexpect-4.2.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/e8/13/d0b0599099d6cd23663043a2a0bb7c61e58c6ba359b2656e6fb000ef5b98/pexpect-4.2.1.tar.gz";
      sha256 = "3d132465a75b57aa818341c6521392a06cc660feb3988d7f1074f39bd23c9a92";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."ptyprocess"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.isc;
      description = "Pexpect allows easy control of interactive console applications.";
    };
  };



  "pickleshare" = python.mkDerivation {
    name = "pickleshare-0.7.4";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/69/fe/dd137d84daa0fd13a709e448138e310d9ea93070620c9db5454e234af525/pickleshare-0.7.4.tar.gz";
      sha256 = "84a9257227dfdd6fe1b4be1319096c20eb85ff1e82c7932f36efccfe1b09737b";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "Tiny 'shelve'-like database with concurrency support";
    };
  };



  "prompt-toolkit" = python.mkDerivation {
    name = "prompt-toolkit-1.0.9";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/83/14/5ac258da6c530eca02852ee25c7a9ff3ca78287bb4c198d0d0055845d856/prompt_toolkit-1.0.9.tar.gz";
      sha256 = "cd6523b36adc174cc10d54b1193eb626b4268609ff6ea92c15bcf1996609599c";
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



  "psycopg2" = python.mkDerivation {
    name = "psycopg2-2.6.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/7b/a8/dc2d50a6f37c157459cd18bab381c8e6134b9381b50fbe969997b2ae7dbc/psycopg2-2.6.2.tar.gz";
      sha256 = "70490e12ed9c5c818ecd85d185d363335cc8a8cbf7212e3c185431c79ff8c05c";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.lgpl2;
      description = "psycopg2 - Python-PostgreSQL Database Adapter";
    };
  };



  "ptyprocess" = python.mkDerivation {
    name = "ptyprocess-0.5.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/db/d7/b465161910f3d1cef593c5e002bff67e0384898f597f1a7fdc8db4c02bf6/ptyprocess-0.5.1.tar.gz";
      sha256 = "0530ce63a9295bfae7bd06edc02b6aa935619f486f0f1dc0972f516265ee81a6";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = "";
      description = "Run a subprocess in a pseudo terminal";
    };
  };



  "py" = python.mkDerivation {
    name = "py-1.4.32";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/93/bd/8a90834a287e0c1682eab8e20ada672e4f4cf7d5b99f2833ddbf31ed1a6d/py-1.4.32.tar.gz";
      sha256 = "c4b89fd1ff1162375115608d01f77c38cca1d0f28f37fd718005e19b28be41a7";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "library with cross-python path, ini-parsing, io, code, log facilities";
    };
  };



  "pycodestyle" = python.mkDerivation {
    name = "pycodestyle-2.2.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/43/9f/56e824b197398582b0c1aaaa2272560bc51f395fe3e45e1dd88de4bb24dc/pycodestyle-2.2.0.tar.gz";
      sha256 = "df81dc3293e0123e2e8d1f2aaf819600e4ae287d8b3af8b72181af50257e5d9a";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "Python style guide checker";
    };
  };



  "pyflakes" = python.mkDerivation {
    name = "pyflakes-1.3.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/9f/48/927b1bf3e15d3dadfcfafb505177a62cdabcb78cf7eac4f31f180d5b1e26/pyflakes-1.3.0.tar.gz";
      sha256 = "a4f93317c97a9d9ed71d6ecfe08b68e3de9fea3f4d94dcd1d9d83ccbf929bc31";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "passive checker of Python programs";
    };
  };



  "pyparsing" = python.mkDerivation {
    name = "pyparsing-2.1.10";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/38/bb/bf325351dd8ab6eb3c3b7c07c3978f38b2103e2ab48d59726916907cd6fb/pyparsing-2.1.10.tar.gz";
      sha256 = "811c3e7b0031021137fc83e051795025fcb98674d07eb8fe922ba4de53d39188";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "Python parsing module";
    };
  };



  "pytest" = python.mkDerivation {
    name = "pytest-3.0.6";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/68/9c/c06dc051b39b817efd31e4c589df7780f7b287d96fab67e90be1f614fc0a/pytest-3.0.6.tar.gz";
      sha256 = "643434a9f1a188271da35e20064cb8b6c5440976c5bb541dc7b5b0e3cf75d940";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."py"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "pytest: simple powerful testing with Python";
    };
  };



  "pytest-runner" = python.mkDerivation {
    name = "pytest-runner-2.10.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/3d/dd/e491ac188a79b4d18628b1f9aa5df3603be72c3a02ae3e1dd5e081cb7ccc/pytest-runner-2.10.1.tar.gz";
      sha256 = "ecc9549ed1ce9bbfc9e7c9bad33d3f9fa91da2334632070a191a35aa96f0be35";
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



  "python-editor" = python.mkDerivation {
    name = "python-editor-1.0.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/65/1e/adf6e000ea5dc909aa420352d6ba37f16434c8a3c2fa030445411a1ed545/python-editor-1.0.3.tar.gz";
      sha256 = "a3c066acee22a1c94f63938341d4fb374e3fdd69366ed6603d7b24bed1efc565";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = "License :: OSI Approved :: Apache Software License";
      description = "Programmatically open an editor, capture the result.";
    };
  };



  "requests" = python.mkDerivation {
    name = "requests-2.13.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/16/09/37b69de7c924d318e51ece1c4ceb679bf93be9d05973bb30c35babd596e2/requests-2.13.0.tar.gz";
      sha256 = "5722cd09762faa01276230270ff16af7acf7c5c45d623868d9ba116f15791ce8";
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



  "responses" = python.mkDerivation {
    name = "responses-0.5.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/09/e4/ae639e37d9d35903fdeda416d7f9c9e3a0331895d574b4fe6632a27c9190/responses-0.5.1.tar.gz";
      sha256 = "8cad64c45959a651ceaf0023484bd26180c927fea64a81e63d334ddf6377ecea";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."cookies"
      self."flake8"
      self."pytest"
      self."requests"
      self."six"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "A utility library for mocking out the `requests` Python library.";
    };
  };



  "setuptools-scm" = python.mkDerivation {
    name = "setuptools-scm-1.15.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/80/b7/31b6ae5fcb188e37f7e31abe75f9be90490a5456a72860fa6e643f8a3cbc/setuptools_scm-1.15.0.tar.gz";
      sha256 = "daf12d05aa2155a46aa357453757ffdc47d87f839e62114f042bceac6a619e2f";
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



  "simplegeneric" = python.mkDerivation {
    name = "simplegeneric-0.8.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/3d/57/4d9c9e3ae9a255cd4e1106bb57e24056d3d0709fc01b2e3e345898e49d5b/simplegeneric-0.8.1.zip";
      sha256 = "dc972e06094b9af5b855b3df4a646395e43d1c9d0d39ed345b7393560d0b9173";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.zpt21;
      description = "Simple generic functions (similar to Python's own len(), pickle.dump(), etc.)";
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



  "strict-rfc3339" = python.mkDerivation {
    name = "strict-rfc3339-0.7";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/56/e4/879ef1dbd6ddea1c77c0078cd59b503368b0456bcca7d063a870ca2119d3/strict-rfc3339-0.7.tar.gz";
      sha256 = "5cad17bedfc3af57b399db0fed32771f18fc54bbd917e85546088607ac5e1277";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.gpl3;
      description = "Strict, simple, lightweight RFC3339 functions";
    };
  };



  "structlog" = python.mkDerivation {
    name = "structlog-16.1.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/3d/d8/90e87637a53ebcb0bbc78b76bceea2f7e8bd98de80feefec7471e38dccf2/structlog-16.1.0.tar.gz";
      sha256 = "b44dfaadcbab84e6bb97bd9b263f61534a79611014679757cd93e2359ee7be01";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."six"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "Structured Logging for Python";
    };
  };



  "swagger-spec-validator" = python.mkDerivation {
    name = "swagger-spec-validator-2.0.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/98/79/b3243192c42cf3ce983e76f2bf38b3dc343f594f35dec6ec3793055f50b8/swagger_spec_validator-2.0.2.tar.gz";
      sha256 = "1947d671cac6096eb578d28767209a65e02a4d24081bf6fc605f09ed6ae1d66b";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."jsonschema"
      self."six"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "Validation of Swagger specifications";
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



  "traitlets" = python.mkDerivation {
    name = "traitlets-4.3.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/b1/d6/5b5aa6d5c474691909b91493da1e8972e309c9f01ecfe4aeafd272eb3234/traitlets-4.3.1.tar.gz";
      sha256 = "ba8c94323ccbe8fd792e45d8efe8c95d3e0744cc8c085295b607552ab573724c";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."decorator"
      self."ipython-genutils"
      self."pytest"
      self."six"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Traitlets Python config system";
    };
  };



  "vcversioner" = python.mkDerivation {
    name = "vcversioner-2.16.0.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/c5/cc/33162c0a7b28a4d8c83da07bc2b12cee58c120b4a9e8bba31c41c8d35a16/vcversioner-2.16.0.0.tar.gz";
      sha256 = "dae60c17a479781f44a4010701833f1829140b1eeccd258762a74974aa06e19b";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.isc;
      description = "Use version control tags to discover version numbers";
    };
  };



  "wcwidth" = python.mkDerivation {
    name = "wcwidth-0.1.7";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/55/11/e4a2bb08bb450fdbd42cc709dd40de4ed2c472cf0ccb9e64af22279c5495/wcwidth-0.1.7.tar.gz";
      sha256 = "3df37372226d6e63e1b1e1eda15c594bca98a22d33a23832a90998faa96bc65e";
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



  "yarl" = python.mkDerivation {
    name = "yarl-0.8.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/10/1b/be30529bde22c85c2975a4e21cf7f13edbcb291350fbbde8bc13938620c8/yarl-0.8.1.tar.gz";
      sha256 = "9f0397ae540124bf16a8a5b89bc3ea1c07f8ae70c3e44231a40a9edd254d5712";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."multidict"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "Yet another URL library";
    };
  };

}