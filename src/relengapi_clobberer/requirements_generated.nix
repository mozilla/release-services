# generated using pypi2nix tool (version: 1.4.0.dev0)
#
# COMMAND:
#   pypi2nix -v -V 3.5 -E postgresql -r requirements.txt -r requirements-setup.txt -r requirements-dev.txt -r requirements-prod.txt
#

{ pkgs, python, commonBuildInputs ? [], commonDoCheck ? false }:

self: {

  "Flask" = python.mkDerivation {
    name = "Flask-0.11.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/55/8a/78e165d30f0c8bb5d57c429a30ee5749825ed461ad6c959688872643ffb3/Flask-0.11.1.tar.gz";
      sha256= "b4713f2bfb9ebc2966b8a49903ae0d3984781d5c878591cf2f7b484d28756b0e";
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



  "Flask-Cache" = python.mkDerivation {
    name = "Flask-Cache-0.13.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/91/c4/f71095437bd4b691c63f240e72a20c57e2c216085cbc271f79665885d3da/Flask-Cache-0.13.1.tar.gz";
      sha256= "90126ca9bc063854ef8ee276e95d38b2b4ec8e45fd77d5751d37971ee27c7ef4";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Flask"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Adds cache support to your Flask application";
    };
  };



  "Flask-Cors" = python.mkDerivation {
    name = "Flask-Cors-2.1.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/99/c3/a65908bc5a031652248dfdb1fd4814391e7b8efca704a94008d764c45292/Flask-Cors-2.1.2.tar.gz";
      sha256= "f262e73adce557b2802a64054c82a0395576c88fbb944e3a9e1e2147140aa639";
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
    name = "Flask-Login-0.3.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/06/e6/61ed90ed8ce6752b745ed13fac3ba407dc9db95dfa2906edc8dd55dde454/Flask-Login-0.3.2.tar.gz";
      sha256= "e72eff5c35e5a31db1aeca1db5d2501be702674ea88e8f223b5d2b11644beee6";
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



  "Flask-SQLAlchemy" = python.mkDerivation {
    name = "Flask-SQLAlchemy-2.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/b3/52/227aaf4e8cebb153e239c518a9e916590b2fe0e4350e6b02d92b546b69b7/Flask-SQLAlchemy-2.1.tar.gz";
      sha256= "c5244de44cc85d2267115624d83faef3f9e8f088756788694f305a5d5ad137c5";
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



  "Jinja2" = python.mkDerivation {
    name = "Jinja2-2.8";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/f2/2f/0b98b06a345a761bec91a079ccae392d282690c2d8272e708f4d10829e22/Jinja2-2.8.tar.gz";
      sha256= "bc1ff2ff88dbfacefde4ddde471d1417d3b304e8df103a7a9437d47269201bf4";
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
      sha256= "87da2515a6b3db866283cb9d4e5a6ec44e52a1d556ebb2ea3b6e7e704b5f1872";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Jinja2"
      self."SQLAlchemy"
      self."redis"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "A logging replacement for Python";
    };
  };



  "MarkupSafe" = python.mkDerivation {
    name = "MarkupSafe-0.23";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/c0/41/bae1254e0396c0cc8cf1751cb7d9afc90a602353695af5952530482c963f/MarkupSafe-0.23.tar.gz";
      sha256= "a4ec1aff59b95a14b45eb2e23761a0179e98319da5a7eb76b56ea8cdc7b871c3";
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
    name = "PyYAML-3.11";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/75/5e/b84feba55e20f8da46ead76f14a3943c8cb722d40360702b2365b91dec00/PyYAML-3.11.tar.gz";
      sha256= "c36c938a872e5ff494938b33b14aaa156cb439ec67548fcab3535bb78b0846e8";
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



  "SQLAlchemy" = python.mkDerivation {
    name = "SQLAlchemy-1.0.14";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/aa/cb/e3990b9da48facbe48b80a281a51fb925ff84aaaca44d368d658b0160fcf/SQLAlchemy-1.0.14.tar.gz";
      sha256= "da4d1a39c1e99c7fecc2aaa3a050094b6aa7134de7d89f77e6216e7abd1705b3";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "Database Abstraction Library";
    };
  };



  "Werkzeug" = python.mkDerivation {
    name = "Werkzeug-0.11.10";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/b7/7f/44d3cfe5a12ba002b253f6985a4477edfa66da53787a2a838a40f6415263/Werkzeug-0.11.10.tar.gz";
      sha256= "cc64dafbacc716cdd42503cf6c44cb5a35576443d82f29f6829e5c49264aeeee";
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
    name = "aiohttp-0.22.5";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/55/9d/38fb3cb174f4723b50a3f0593e18a51418c9a73a7857fdcaee46b83ff1c4/aiohttp-0.22.5.tar.gz";
      sha256= "9c51af030c866f91e18a219614e39d345db4483ed9860389d0536d74d04b0d3b";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."chardet"
      self."multidict"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "http client/server for asyncio";
    };
  };



  "chardet" = python.mkDerivation {
    name = "chardet-2.3.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/7d/87/4e3a3f38b2f5c578ce44f8dc2aa053217de9f0b6d737739b0ddac38ed237/chardet-2.3.0.tar.gz";
      sha256= "e53e38b3a4afe6d1132de62b7400a4ac363452dc5dfcf8d88e8e0cce663c68aa";
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
      sha256= "cc6a19da8ebff6e7074f731447ef7e112bd23adf3de5c597cf9989f2fd8defe9";
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



  "connexion" = python.mkDerivation {
    name = "connexion-1.0.109";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/7e/cf/818a9784400c6eaf9e8f6b81b875b9ed0394f2b2e96f0e48ced4574a93ed/connexion-1.0.109.tar.gz";
      sha256= "b6d2b320020258fbc3adf21c7ecec25431bd6e93c4f085081fab4b37e821066a";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."Flask"
      self."PyYAML"
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



  "decorator" = python.mkDerivation {
    name = "decorator-4.0.10";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/13/8a/4eed41e338e8dcc13ca41c94b142d4d20c0de684ee5065523fee406ce76f/decorator-4.0.10.tar.gz";
      sha256= "9c6e98edcb33499881b86ede07d9968c81ab7c769e28e9af24075f0a5379f070";
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
    name = "flake8-3.0.4";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/b0/56/48727b2a6c92b7e632180cf2c1411a0de7cf4f636b4f844c6c46f7edc86b/flake8-3.0.4.tar.gz";
      sha256= "b4c210c998f07d6ff24325dd91fbc011f2c37bcd6bf576b188de01d8656e970d";
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
      sha256= "813f6916d18a4c8e90efde72f419308b357692f81333cb1125f80013d22fb618";
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
    name = "ipdb-0.10.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/eb/0a/0a37dc19572580336ad3813792c0d18c8d7117c2d66fc63c501f13a7a8f8/ipdb-0.10.1.tar.gz";
      sha256= "bb2948e726dbfb2687f4a582088b3f170b2556ba8e54ae1231c783c97e99ec87";
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
    name = "ipython-5.0.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/09/2e/870d1058768f5240062beb0bd2ff789ac689923501b0dd6b480fb83314fc/ipython-5.0.0.tar.gz";
      sha256= "7ec0737169c74056c7fc8298246db5478a2d6c90cfd19c3253222112357545df";
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
      sha256= "3a0624a251a26463c9dfa0ffa635ec51c4265380980d9a50d65611c3c2bd82a6";
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
      sha256= "cbb3fcf8d3e33df861709ecaf89d9e6629cff0a217bc2848f1b41cd30d360519";
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
      sha256= "36673ac378feed3daa5956276a829699056523d7961027911f064b52255ead41";
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
    name = "mccabe-0.5.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/f1/b7/ff36d1a163079688633a776e1717b5459caccbb68973afab2aa8345ac40f/mccabe-0.5.2.tar.gz";
      sha256= "3473f06c8b757bbb5cdf295099bf64032e5f7d6fe0ec2f97ee9b23cb0a435aff";
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
    name = "mohawk-0.3.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/6e/c0/fef11cfffdc7729f4dc3dfff70468de0d604c3e2bdcf3170c76b90a7ae1e/mohawk-0.3.3.tar.gz";
      sha256= "ed68517c20c909abe64bbceb89137b97c1df8c55d95be1c53dfd6c9264003ad0";
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
    name = "multidict-1.2.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/fd/5b/3dd32b8e53703ff7a27a72e9a118e7f78c14a171554ec8c99dd4759c4018/multidict-1.2.2.tar.gz";
      sha256= "2fc5fab0dd14d4b8193bfc003b33aa14e0d0cbc97d51ba58aa5fd52b1cb9a6a3";
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
    name = "newrelic-2.68.0.50";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/a0/54/c241f39e4919faa7d7afdf85fd9364d92df6282b3384762020d8a547ca1f/newrelic-2.68.0.50.tar.gz";
      sha256= "3ac02183910fe41ab75485d05474164890b993d082dca5847b0e6d24cf166f89";
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



  "pexpect" = python.mkDerivation {
    name = "pexpect-4.2.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/b3/7b/7b3659b9d7059d6d21e23b2464c5c84bffd4a34450cbf0ed19c9a8a4a52f/pexpect-4.2.0.tar.gz";
      sha256= "bf6816b8cc8d301a499e7adf338828b39bc7548eb64dbed4dd410ed93d95f853";
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
    name = "pickleshare-0.7.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/5d/29/5f3eb419067a98fe98d78a7e309fef03abceb2dc3e3587c88e2ca704ba20/pickleshare-0.7.3.tar.gz";
      sha256= "b9710d01f777b1bf3b69c8f889b1d05a5145668f79e980cbd0f849e059edd274";
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



  "psycopg2" = python.mkDerivation {
    name = "psycopg2-2.6.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/7b/a8/dc2d50a6f37c157459cd18bab381c8e6134b9381b50fbe969997b2ae7dbc/psycopg2-2.6.2.tar.gz";
      sha256= "70490e12ed9c5c818ecd85d185d363335cc8a8cbf7212e3c185431c79ff8c05c";
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
      sha256= "0530ce63a9295bfae7bd06edc02b6aa935619f486f0f1dc0972f516265ee81a6";
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



  "pycodestyle" = python.mkDerivation {
    name = "pycodestyle-2.0.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/db/b1/9f798e745a4602ab40bf6a9174e1409dcdde6928cf800d3aab96a65b1bbf/pycodestyle-2.0.0.tar.gz";
      sha256= "37f0420b14630b0eaaf452978f3a6ea4816d787c3e6dcbba6fb255030adae2e7";
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
    name = "pyflakes-1.2.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/54/80/6a641f832eb6c6a8f7e151e7087aff7a7c04dd8b4aa6134817942cdda1b6/pyflakes-1.2.3.tar.gz";
      sha256= "2e4a1b636d8809d8f0a69f341acf15b2e401a3221ede11be439911d23ce2139e";
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



  "pytest-runner" = python.mkDerivation {
    name = "pytest-runner-2.9";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/11/d4/c335ddf94463e451109e3494e909765c3e5205787b772e3b25ee8601b86a/pytest-runner-2.9.tar.gz";
      sha256= "50378de59b02f51f64796d3904dfe71b9dc6f06d88fc6bfbd5c8e8366ae1d131";
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



  "redis" = python.mkDerivation {
    name = "redis-2.10.5";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/68/44/5efe9e98ad83ef5b742ce62a15bea609ed5a0d1caf35b79257ddb324031a/redis-2.10.5.tar.gz";
      sha256= "5dfbae6acfc54edf0a7a415b99e0b21c0a3c27a7f787b292eea727b1facc5533";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "Python client for Redis key-value store";
    };
  };



  "requests" = python.mkDerivation {
    name = "requests-2.11.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/8d/66/649f861f980c0a168dd4cccc4dd0ed8fa5bd6c1bed3bea9a286434632771/requests-2.11.0.tar.gz";
      sha256= "b2ff053e93ef11ea08b0e596a1618487c4e4c5f1006d7a1706e3671c57dea385";
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
      sha256= "8c45f738a23410c5276b0ed9294af607f491e4260589f1eb90df8312e23819bf";
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
      sha256= "dc972e06094b9af5b855b3df4a646395e43d1c9d0d39ed345b7393560d0b9173";
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



  "slugid" = python.mkDerivation {
    name = "slugid-1.0.7";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/dd/96/b05c6d357f8d6932bea2b360537360517d1154b82cc71b8eccb70b28bdde/slugid-1.0.7.tar.gz";
      sha256= "6dab3c7eef0bb423fb54cb7752e0f466ddd0ee495b78b763be60e8a27f69e779";
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
      sha256= "5cad17bedfc3af57b399db0fed32771f18fc54bbd917e85546088607ac5e1277";
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
      sha256= "b44dfaadcbab84e6bb97bd9b263f61534a79611014679757cd93e2359ee7be01";
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
      sha256= "1947d671cac6096eb578d28767209a65e02a4d24081bf6fc605f09ed6ae1d66b";
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
      sha256= "d4fe5e2a44fe27e195b92830ece0a6eb9eb7ad9dc556a0cb16f6f2a6429f1b65";
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
    name = "traitlets-4.2.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/a4/07/9b7636322c152ab1dacae9d38131067523d6ce5ca926a656586f6f947e77/traitlets-4.2.2.tar.gz";
      sha256= "7d7e3070484b2fe490fa55e0acf7023afc5ed9ddabec57405f25c355158e152a";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."decorator"
      self."ipython-genutils"
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
      sha256= "dae60c17a479781f44a4010701833f1829140b1eeccd258762a74974aa06e19b";
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