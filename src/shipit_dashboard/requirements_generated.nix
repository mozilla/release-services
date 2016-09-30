# generated using pypi2nix tool (version: 1.5.0.dev0)
#
# COMMAND:
#   pypi2nix -v -V 3.5 -E postgresql libffi openssl pkgconfig freetype.dev -r requirements.txt -r requirements-setup.txt -r requirements-dev.txt -r requirements-prod.txt
#

{ pkgs, python, commonBuildInputs ? [], commonDoCheck ? false }:

self: {

  "Flask" = python.mkDerivation {
    name = "Flask-0.11.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/55/8a/78e165d30f0c8bb5d57c429a30ee5749825ed461ad6c959688872643ffb3/Flask-0.11.1.tar.gz";
      sha256 = "b4713f2bfb9ebc2966b8a49903ae0d3984781d5c878591cf2f7b484d28756b0e";
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
      sha256 = "90126ca9bc063854ef8ee276e95d38b2b4ec8e45fd77d5751d37971ee27c7ef4";
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
    name = "Flask-Login-0.3.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/06/e6/61ed90ed8ce6752b745ed13fac3ba407dc9db95dfa2906edc8dd55dde454/Flask-Login-0.3.2.tar.gz";
      sha256 = "e72eff5c35e5a31db1aeca1db5d2501be702674ea88e8f223b5d2b11644beee6";
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



  "Jinja2" = python.mkDerivation {
    name = "Jinja2-2.8";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/f2/2f/0b98b06a345a761bec91a079ccae392d282690c2d8272e708f4d10829e22/Jinja2-2.8.tar.gz";
      sha256 = "bc1ff2ff88dbfacefde4ddde471d1417d3b304e8df103a7a9437d47269201bf4";
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



  "SQLAlchemy" = python.mkDerivation {
    name = "SQLAlchemy-1.0.15";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/18/7d/f230ac50198cfe3cdc957c3572a18dc92600047ce707b5b923c56ab92c1b/SQLAlchemy-1.0.15.tar.gz";
      sha256 = "586f5ccf068211795a89ed22d196c5cc3006b6be00261bcac6f584c0b8e0845a";
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
    name = "Werkzeug-0.11.11";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/43/2e/d822b4a4216804519ace92e0368dcfc4b0b2887462d852fdd476b253ecc9/Werkzeug-0.11.11.tar.gz";
      sha256 = "e72c46bc14405cba7a26bd2ce28df734471bc9016bc8b4cb69466c2c14c2f7e5";
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
    name = "aiohttp-1.0.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/9e/98/982208caf31a284f020e9bb3b5f7b13dbd1d122d903b39e91620481de70b/aiohttp-1.0.3.tar.gz";
      sha256 = "5ec0fdf17868bcabfef4effa3ce53c4cfa6108b481585bda88498f46435d5eaa";
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



  "cffi" = python.mkDerivation {
    name = "cffi-1.8.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/0a/f3/686af8873b70028fccf67b15c78fd4e4667a3da995007afc71e786d61b0a/cffi-1.8.3.tar.gz";
      sha256 = "c321bd46faa7847261b89c0469569530cad5a41976bb6dba8202c0159f476568";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."pycparser"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "Foreign Function Interface for Python calling C code.";
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



  "clickclick" = python.mkDerivation {
    name = "clickclick-1.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/ee/b6/ad6a25ab897a17809e5c6b9cc45f6e19b162645129c02a4e15b4d32fb874/clickclick-1.2.tar.gz";
      sha256 = "3d436615e3cbc55d04b02f368a76cd3729c523e96e3353455d2bbfc95d5d703d";
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
    name = "connexion-1.0.128";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/84/1d/4b7bd595aa6d53ab24e680633fe9750f1b1431ae35d25e382342b3191b0b/connexion-1.0.128.tar.gz";
      sha256 = "78b4df8a95168ddc0fad3f7bf07a8a45e573421c1eaaec88ab76b3842ed6bd88";
    };
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



  "cryptography" = python.mkDerivation {
    name = "cryptography-1.5.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/03/1a/60984cb85cc38c4ebdfca27b32a6df6f1914959d8790f5a349608c78be61/cryptography-1.5.2.tar.gz";
      sha256 = "eb8875736734e8e870b09be43b17f40472dc189b1c422a952fa8580768204832";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."cffi"
      self."flake8"
      self."idna"
      self."pyasn1"
      self."pyasn1-modules"
      self."pytz"
      self."six"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "cryptography is a package which provides cryptographic recipes and primitives to Python developers.";
    };
  };



  "cycler" = python.mkDerivation {
    name = "cycler-0.10.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/c2/4b/137dea450d6e1e3d474e1d873cd1d4f7d3beed7e0dc973b06e8e10d32488/cycler-0.10.0.tar.gz";
      sha256 = "cd7b2d1018258d7247a71425e9f26463dfb444d411c39569972f4ce586b0c9d8";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."six"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Composable style cycles";
    };
  };



  "decorator" = python.mkDerivation {
    name = "decorator-4.0.10";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/13/8a/4eed41e338e8dcc13ca41c94b142d4d20c0de684ee5065523fee406ce76f/decorator-4.0.10.tar.gz";
      sha256 = "9c6e98edcb33499881b86ede07d9968c81ab7c769e28e9af24075f0a5379f070";
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



  "elasticsearch" = python.mkDerivation {
    name = "elasticsearch-2.4.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/b0/14/7decd0d5cba7f9b5bf0b421a8c7cde6ade0b1941d524b5be78f61d29b8d6/elasticsearch-2.4.0.tar.gz";
      sha256 = "e71dd7058b940f409068d8d5df2354dc4367436947a28e0e03d35d5c0508c310";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."urllib3"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "Python client for Elasticsearch";
    };
  };



  "flake8" = python.mkDerivation {
    name = "flake8-3.0.4";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/b0/56/48727b2a6c92b7e632180cf2c1411a0de7cf4f636b4f844c6c46f7edc86b/flake8-3.0.4.tar.gz";
      sha256 = "b4c210c998f07d6ff24325dd91fbc011f2c37bcd6bf576b188de01d8656e970d";
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



  "google-api-python-client" = python.mkDerivation {
    name = "google-api-python-client-1.5.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/3f/d0/2ecf9a160ebe7aba392d5bf21b616b204e2c49c79603dfb53c171e9bbe2c/google-api-python-client-1.5.3.tar.gz";
      sha256 = "d916e04969cb1fd6727b9f49290828e9d7162b90c1d5b4be0aed3c171a75d8be";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."httplib2"
      self."oauth2client"
      self."six"
      self."uritemplate"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "Google API Client Library for Python";
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



  "httplib2" = python.mkDerivation {
    name = "httplib2-0.9.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/ff/a9/5751cdf17a70ea89f6dde23ceb1705bfb638fd8cee00f845308bf8d26397/httplib2-0.9.2.tar.gz";
      sha256 = "c3aba1c9539711551f4d83e857b316b5134a1c4ddce98a875b7027be7dd6d988";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "A comprehensive HTTP client library.";
    };
  };



  "icalendar" = python.mkDerivation {
    name = "icalendar-3.10";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/3f/40/a479fd8d450e06ab0965227b3231ac3c4479dbaf424fdbdd1045809dc434/icalendar-3.10.tar.gz";
      sha256 = "472f01da00e1e28eaf0cf03cc872c4cbce22dab50629ea9e72470761c6b45505";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."python-dateutil"
      self."pytz"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "iCalendar parser/generator";
    };
  };



  "idna" = python.mkDerivation {
    name = "idna-2.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/fb/84/8c27516fbaa8147acd2e431086b473c453c428e24e8fb99a1d89ce381851/idna-2.1.tar.gz";
      sha256 = "ed36f281aebf3cd0797f163bb165d84c31507cedd15928b095b1675e2d04c676";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Internationalized Domain Names in Applications (IDNA)";
    };
  };



  "ipdb" = python.mkDerivation {
    name = "ipdb-0.10.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/eb/0a/0a37dc19572580336ad3813792c0d18c8d7117c2d66fc63c501f13a7a8f8/ipdb-0.10.1.tar.gz";
      sha256 = "bb2948e726dbfb2687f4a582088b3f170b2556ba8e54ae1231c783c97e99ec87";
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
      self."numpy"
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



  "libmozdata" = python.mkDerivation {
    name = "libmozdata-0.1.12";
    src = pkgs.fetchurl {
      url = "https://github.com/La0/libmozdata/archive/master.tar.gz";
      sha256 = "1e512551d7626521d9e021e0f15fef20dcd22f012ec85f2e8aacdb7d3288d84c";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."elasticsearch"
      self."google-api-python-client"
      self."httplib2"
      self."icalendar"
      self."matplotlib"
      self."numpy"
      self."oauth2client"
      self."python-dateutil"
      self."requests"
      self."requests-futures"
      self."six"
      self."whatthepatch"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = "MPL2";
      description = "Library to access and aggregate several Mozilla data sources.";
    };
  };



  "matplotlib" = python.mkDerivation {
    name = "matplotlib-1.5.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/75/4e/2374eed18ac34421ccd7b4907080abd3009e112ca2c11b100c18961312e0/matplotlib-1.5.3.tar.gz";
      sha256 = "a0a5dc39f785014f2088fed2c6d2d129f0444f71afbb9c44f7bdf1b14d86ebbc";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."cycler"
      self."numpy"
      self."pyparsing"
      self."python-dateutil"
      self."pytz"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.psfl;
      description = "Python plotting package";
    };
  };



  "mccabe" = python.mkDerivation {
    name = "mccabe-0.5.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/f1/b7/ff36d1a163079688633a776e1717b5459caccbb68973afab2aa8345ac40f/mccabe-0.5.2.tar.gz";
      sha256 = "3473f06c8b757bbb5cdf295099bf64032e5f7d6fe0ec2f97ee9b23cb0a435aff";
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
    name = "multidict-2.1.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/8b/99/a32210e82198db00d071aa207432b898ddd8061000d00d3841a63a734d31/multidict-2.1.2.tar.gz";
      sha256 = "d90367472d55de953d4b8d99029067026418d213a88f43e8b0554d7408188576";
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



  "ndg-httpsclient" = python.mkDerivation {
    name = "ndg-httpsclient-0.4.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/a2/a7/ad1c1c48e35dc7545dab1a9c5513f49d5fa3b5015627200d2be27576c2a0/ndg_httpsclient-0.4.2.tar.gz";
      sha256 = "580987ef194334c50389e0d7de885fccf15605c13c6eecaabd8d6c43768eb8ac";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."pyOpenSSL"
      self."pyasn1"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Provides enhanced HTTPS support for httplib and urllib2 using PyOpenSSL";
    };
  };



  "newrelic" = python.mkDerivation {
    name = "newrelic-2.70.0.51";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/76/0b/b0947f27186a4ed9260ada5bee009ec8e453fdbcff8a031ae8866a61e2fa/newrelic-2.70.0.51.tar.gz";
      sha256 = "54e1da319d4670b4887b463309907cbefeff847a26e378609d04126a14d01b13";
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



  "numpy" = python.mkDerivation {
    name = "numpy-1.11.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/16/f5/b432f028134dd30cfbf6f21b8264a9938e5e0f75204e72453af08d67eb0b/numpy-1.11.2.tar.gz";
      sha256 = "04db2fbd64e2e7c68e740b14402b25af51418fc43a59d9e54172b38b906b0f69";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "NumPy: array processing for numbers, strings, records, and objects.";
    };
  };



  "oauth2client" = python.mkDerivation {
    name = "oauth2client-3.0.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/c0/7b/bc893e35d6ca46a72faa4b9eaac25c687ce60e1fbe978993fe2de1b0ff0d/oauth2client-3.0.0.tar.gz";
      sha256 = "5b5b056ec6f2304e7920b632885bd157fa71d1a7f3ddd00a43b1541a8d1a2460";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."httplib2"
      self."pyasn1"
      self."pyasn1-modules"
      self."rsa"
      self."six"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "OAuth 2.0 client library";
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
    name = "prompt-toolkit-1.0.7";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/dd/55/2fb4883d2b21d072204fd21ca5e6040faa253135554590d0b67380669176/prompt_toolkit-1.0.7.tar.gz";
      sha256 = "ef0b8188179fe7d052161ed274b43e18f5a680ff84d01462293b327e1668d2ef";
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



  "pyOpenSSL" = python.mkDerivation {
    name = "pyOpenSSL-16.1.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/15/1e/79c75db50e57350a7cefb70b110255757e9abd380a50ebdc0cfd853b7450/pyOpenSSL-16.1.0.tar.gz";
      sha256 = "88f7ada2a71daf2c78a4f139b19d57551b4c8be01f53a1cb5c86c2f3bf01355f";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."cryptography"
      self."six"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "Python wrapper module around the OpenSSL library";
    };
  };



  "pyasn1" = python.mkDerivation {
    name = "pyasn1-0.1.9";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/f7/83/377e3dd2e95f9020dbd0dfd3c47aaa7deebe3c68d3857a4e51917146ae8b/pyasn1-0.1.9.tar.gz";
      sha256 = "853cacd96d1f701ddd67aa03ecc05f51890135b7262e922710112f12a2ed2a7f";
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



  "pyasn1-modules" = python.mkDerivation {
    name = "pyasn1-modules-0.0.8";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/60/32/7703bccdba05998e4ff04db5038a6695a93bedc45dcf491724b85b5db76a/pyasn1-modules-0.0.8.tar.gz";
      sha256 = "10561934f1829bcc455c7ecdcdacdb4be5ffd3696f26f468eb6eb41e107f3837";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."pyasn1"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "A collection of ASN.1-based protocols modules.";
    };
  };



  "pycodestyle" = python.mkDerivation {
    name = "pycodestyle-2.0.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/db/b1/9f798e745a4602ab40bf6a9174e1409dcdde6928cf800d3aab96a65b1bbf/pycodestyle-2.0.0.tar.gz";
      sha256 = "37f0420b14630b0eaaf452978f3a6ea4816d787c3e6dcbba6fb255030adae2e7";
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



  "pycparser" = python.mkDerivation {
    name = "pycparser-2.14";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/6d/31/666614af3db0acf377876d48688c5d334b6e493b96d21aa7d332169bee50/pycparser-2.14.tar.gz";
      sha256 = "7959b4a74abdc27b312fed1c21e6caf9309ce0b29ea86b591fd2e99ecdf27f73";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "C parser in Python";
    };
  };



  "pyflakes" = python.mkDerivation {
    name = "pyflakes-1.2.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/54/80/6a641f832eb6c6a8f7e151e7087aff7a7c04dd8b4aa6134817942cdda1b6/pyflakes-1.2.3.tar.gz";
      sha256 = "2e4a1b636d8809d8f0a69f341acf15b2e401a3221ede11be439911d23ce2139e";
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
    name = "pyparsing-2.1.9";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/87/ee/6f3a94d834c82a5c1a74f2fc77775ff05b5fbbf7d97f844e6fff5e2ff94b/pyparsing-2.1.9.tar.gz";
      sha256 = "93326f5490bcfe7069806ff342692e75f72529cfa82f20683b5fceeb5d4a7fc2";
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



  "python-dateutil" = python.mkDerivation {
    name = "python-dateutil-2.5.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/3e/f5/aad82824b369332a676a90a8c0d1e608b17e740bbb6aeeebca726f17b902/python-dateutil-2.5.3.tar.gz";
      sha256 = "1408fdb07c6a1fa9997567ce3fcee6a337b39a503d80699e0f213de4aa4b32ed";
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



  "redis" = python.mkDerivation {
    name = "redis-2.10.5";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/68/44/5efe9e98ad83ef5b742ce62a15bea609ed5a0d1caf35b79257ddb324031a/redis-2.10.5.tar.gz";
      sha256 = "5dfbae6acfc54edf0a7a415b99e0b21c0a3c27a7f787b292eea727b1facc5533";
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
    name = "requests-2.11.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/2e/ad/e627446492cc374c284e82381215dcd9a0a87c4f6e90e9789afefe6da0ad/requests-2.11.1.tar.gz";
      sha256 = "5acf980358283faba0b897c73959cecf8b841205bb4b2ad3ef545f46eae1a133";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."ndg-httpsclient"
      self."pyOpenSSL"
      self."pyasn1"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.asl20;
      description = "Python HTTP for Humans.";
    };
  };



  "requests-futures" = python.mkDerivation {
    name = "requests-futures-0.9.7";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/2c/f0/d9a6d4472286405956dd5ac6279fe932a86151df9816bc35afe601495819/requests-futures-0.9.7.tar.gz";
      sha256 = "a9ca2c3480b6fac29ec5de59c146742e2ab2b60f8c68581766094edb52ea7bad";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."requests"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = "License :: OSI Approved :: Apache Software License";
      description = "Asynchronous Python HTTP for Humans.";
    };
  };



  "rsa" = python.mkDerivation {
    name = "rsa-3.4.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/14/89/adf8b72371e37f3ca69c6cb8ab6319d009c4a24b04a31399e5bd77d9bb57/rsa-3.4.2.tar.gz";
      sha256 = "25df4e10c263fb88b5ace923dd84bf9aa7f5019687b5e55382ffcdb8bede9db5";
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



  "simplejson" = python.mkDerivation {
    name = "simplejson-3.8.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/f0/07/26b519e6ebb03c2a74989f7571e6ae6b82e9d7d81b8de6fcdbfc643c7b58/simplejson-3.8.2.tar.gz";
      sha256 = "d58439c548433adcda98e695be53e526ba940a4b9c44fb9a05d92cd495cdd47f";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "Simple, fast, extensible JSON encoder/decoder for Python";
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
      self."six"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "Traitlets Python config system";
    };
  };



  "uritemplate" = python.mkDerivation {
    name = "uritemplate-0.6";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/5a/6d/66aed916219c1a25e12a01457ea5442f80e54ed3844ef688b25e20dada5f/uritemplate-0.6.tar.gz";
      sha256 = "a30e230aeb7ebedbcb5da9999a17fa8a30e512e6d5b06f73d47c6e03c8e357fd";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."simplejson"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = "License :: OSI Approved :: Apache Software License";
      description = "URI Templates";
    };
  };



  "urllib3" = python.mkDerivation {
    name = "urllib3-1.18";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/8f/45/7434a6a44d42744b74fb969a39720f0c3d4f31f921737e51a69d8b15c859/urllib3-1.18.tar.gz";
      sha256 = "d30dd4d1cbbc36ebab6e4a2076820cfe0c60f10adf087fecbc5a3edae79fdc81";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."cryptography"
      self."idna"
      self."pyOpenSSL"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "HTTP library with thread-safe connection pooling, file post, and more.";
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



  "whatthepatch" = python.mkDerivation {
    name = "whatthepatch-0.0.4";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/12/a1/4b8a0cb58402a790ceda78ef4af9614e164979675bd052230d6326af1b0e/whatthepatch-0.0.4.tar.gz";
      sha256 = "091cc0111e9361b2ba1925eef41b4b3aeeb83f19b06ff031870f75a4423d0de0";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "A patch parsing library.";
    };
  };

}