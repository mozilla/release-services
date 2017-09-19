# generated using pypi2nix tool (version: 1.6.0)
#
# COMMAND:
#   pypi2nix -v -V 3.5 -s six packaging appdirs -E libffi openssl pkgconfig freetype.dev -r /home/lao/dev/mozilla/relengapi/src/shipit_pulse_listener/requirements.txt -r /home/lao/dev/mozilla/relengapi/src/shipit_pulse_listener/requirements-dev.txt -r /home/lao/dev/mozilla/relengapi/src/shipit_pulse_listener/requirements-nix.txt
#

{ pkgs, python, commonBuildInputs ? [], commonDoCheck ? false }:

self: {

  "aioamqp" = python.mkDerivation {
    name = "aioamqp-0.8.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/79/6b/255c936283f73151c6767b1b5ff5542c94019848c53083ea7522c99e8985/aioamqp-0.8.2.tar.gz";
      sha256 = "8d3da99ef396f92e2d00ab51c3ac04de2beb8bac088be78e3fa321c5a237d47f";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "AMQP implementation using asyncio";
    };
  };



  "aiohttp" = python.mkDerivation {
    name = "aiohttp-1.3.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/41/42/76a4cff04488799e78d37c5bb3b607e36d2c4686141621002d2479b54dbe/aiohttp-1.3.1.tar.gz";
      sha256 = "e147b0cea568773443683becce9de4071506431118609b5d477fe61508417af1";
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



  "cffi" = python.mkDerivation {
    name = "cffi-1.9.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/a1/32/e3d6c3a8b5461b903651dd6ce958ed03c093d2e00128e3f33ea69f1d7965/cffi-1.9.1.tar.gz";
      sha256 = "563e0bd53fda03c151573217b3a49b3abad8813de9dd0632e10090f6190fdaf8";
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



  "cryptography" = python.mkDerivation {
    name = "cryptography-1.7.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/99/df/71c7260003f5c469cec3db4c547115df39e9ce6c719a99e067ba0e78fd8a/cryptography-1.7.2.tar.gz";
      sha256 = "878cb68b3da3d493ffd68f36db11c29deee623671d3287c3f8d685117ffda9a9";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."cffi"
      self."flake8"
      self."idna"
      self."pyasn1"
      self."pyasn1-modules"
      self."pytest"
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



  "elasticsearch" = python.mkDerivation {
    name = "elasticsearch-5.2.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/e7/b5/a77098b1f248dbc6407a53d51bf1980ab91718cd93c662cdb1ed529a1278/elasticsearch-5.2.0.tar.gz";
      sha256 = "45d9f8fbe0878a1b7493afeb20f4f6677a43982776ed1a77d9373e9c5b9de966";
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
    name = "flake8-3.3.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/47/64/382631de5fd8dab367bedeff6b5b55fd9a7c883daa44f4032636e2d203ca/flake8-3.3.0.tar.gz";
      sha256 = "b907a26dcf5580753d8f80f1be0ec1d5c45b719f7bac441120793d1a70b03f12";
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
    name = "google-api-python-client-1.6.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/e8/04/4bb1672918e4fc6d6a8201bdaf986b9fb4763f2a47b11496186dbbbd40ce/google-api-python-client-1.6.2.tar.gz";
      sha256 = "8c2f50f8057571a5f817c74820cadb754d47799c5a4ea463c1500fe8e092c1ae";
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



  "httplib2" = python.mkDerivation {
    name = "httplib2-0.10.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/e4/2e/a7e27d2c36076efeb8c0e519758968b20389adf57a9ce3af139891af2696/httplib2-0.10.3.tar.gz";
      sha256 = "e404d3b7bd86c1bc931906098e7c1305d6a3a6dcef141b8bb1059903abb3ceeb";
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
    name = "icalendar-3.11.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/e7/e7/71810ac9d3d5a062d3d7d16090ce2ea3e7877c2124afe23f9f7b8e2ffedd/icalendar-3.11.2.tar.gz";
      sha256 = "4f1df994cc0fe7ce63fec7adf1d9b3074b784faf3b1e702e7112cfb4b2f12c9f";
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
    name = "idna-2.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/94/fe/efb1cb6f505e1a560b3d080ae6b9fddc11e7c542d694ce4635c49b1ccdcb/idna-2.2.tar.gz";
      sha256 = "0ac27740937d86850010e035c6a10a564158a5accddf1aa24df89b0309252426";
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



  "libmozdata" = python.mkDerivation {
    name = "libmozdata-0.1.31";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/c0/38/47954d9f4d95e8f54357b7f344ade6767a62b6d95868f27b22edb42d8634/libmozdata-0.1.31.tar.gz";
      sha256 = "11a69e600c09c85fe33ee27ab40a7fc14f8bae658e69f52cb3509614273d8747";
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
    name = "matplotlib-2.0.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/79/a9/db688816150a6ef91fd9ce284c828467f7271c7dd5982753a73a8e1aaafa/matplotlib-2.0.0.tar.gz";
      sha256 = "36cf0985829c1ab2b8b1dae5e2272e53ae681bf33ab8bedceed4f0565af5f813";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."cycler"
      self."numpy"
      self."pyparsing"
      self."python-dateutil"
      self."pytz"
      self."six"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.psfl;
      description = "Python plotting package";
    };
  };



  "mccabe" = python.mkDerivation {
    name = "mccabe-0.6.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/06/18/fa675aa501e11d6d6ca0ae73a101b2f3571a565e0f7d38e062eec18a91ee/mccabe-0.6.1.tar.gz";
      sha256 = "dd8d182285a0fe56bace7f45b5e7d1a6ebcbf524e8f3bd87eb0f125271b8831f";
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



  "numpy" = python.mkDerivation {
    name = "numpy-1.12.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/b7/9d/8209e555ea5eb8209855b6c9e60ea80119dab5eff5564330b35aa5dc4b2c/numpy-1.12.0.zip";
      sha256 = "ff320ecfe41c6581c8981dce892fe6d7e69806459a899e294e4bf8229737b154";
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
    name = "oauth2client-4.0.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/c2/ce/7aaf19d8b856191e2e1885201fe45f3dc57b97f5ec5bc98ef2cc15472918/oauth2client-4.0.0.tar.gz";
      sha256 = "80be5420889694634b8517b4acd3292ace881d9d1aa9d590d37ec52faec238c7";
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



  "pyOpenSSL" = python.mkDerivation {
    name = "pyOpenSSL-16.2.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/0c/d6/b1fe519846a21614fa4f8233361574eddb223e0bc36b182140d916acfb3b/pyOpenSSL-16.2.0.tar.gz";
      sha256 = "7779a3bbb74e79db234af6a08775568c6769b5821faecf6e2f4143edb227516e";
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
    name = "pyasn1-0.2.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/57/f7/c18a86169bb9995a69195177b23e736776b347fd92592da0c3cac9f1a724/pyasn1-0.2.2.tar.gz";
      sha256 = "6b42f96b942406712e0be5ea2bbbc57d8f30c7835a4904c9c195cc669736d435";
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
    name = "pycodestyle-2.3.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/e1/88/0e2cbf412bd849ea6f1af1f97882add46a374f4ba1d2aea39353609150ad/pycodestyle-2.3.1.tar.gz";
      sha256 = "682256a5b318149ca0d2a9185d365d8864a768a28db66a84a2ea946bcc426766";
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
    name = "pycparser-2.17";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/be/64/1bb257ffb17d01f4a38d7ce686809a736837ad4371bcc5c42ba7a715c3ac/pycparser-2.17.tar.gz";
      sha256 = "0aac31e917c24cb3357f5a4d5566f2cc91a19ca41862f6c3c22dc60a629673b6";
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
    name = "pyflakes-1.5.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/5b/b7/dcd6ebc826065ca4ccd2406aac4378e1df6eb91124625d45d520219932a1/pyflakes-1.5.0.tar.gz";
      sha256 = "aa0d4dff45c0cc2214ba158d29280f8fa1129f3e87858ef825930845146337f4";
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
    name = "pytest-runner-2.11.1";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/9e/4d/08889e5e27a9f5d6096b9ad257f4dea1faabb03c5ded8f665ead448f5d8a/pytest-runner-2.11.1.tar.gz";
      sha256 = "983a31eab45e375240e250161a556163bc8d250edaba97960909338c273a89b3";
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
    name = "python-dateutil-2.6.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/51/fc/39a3fbde6864942e8bb24c93663734b74e281b984d1b8c4f95d64b0c21f6/python-dateutil-2.6.0.tar.gz";
      sha256 = "62a2f8df3d66f878373fd0072eacf4ee52194ba302e00082828e0d263b0418d2";
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
    name = "pytz-2016.10";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/d0/e1/aca6ef73a7bd322a7fc73fd99631ee3454d4fc67dc2bee463e2adf6bb3d3/pytz-2016.10.tar.bz2";
      sha256 = "7016b2c4fa075c564b81c37a252a5fccf60d8964aa31b7f5eae59aeb594ae02b";
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



  "requests" = python.mkDerivation {
    name = "requests-2.13.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/16/09/37b69de7c924d318e51ece1c4ceb679bf93be9d05973bb30c35babd596e2/requests-2.13.0.tar.gz";
      sha256 = "5722cd09762faa01276230270ff16af7acf7c5c45d623868d9ba116f15791ce8";
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
    name = "taskcluster-1.0.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/d8/00/aac389ae5f2db76b029d55d36d394e272486894d155073369c4e0b272619/taskcluster-1.0.2.tar.gz";
      sha256 = "11cfd462a333e0a084f94c9ce55e349036dbcf04656767f9773da7d148aa5115";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."aiohttp"
      self."async-timeout"
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



  "uritemplate" = python.mkDerivation {
    name = "uritemplate-3.0.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/cd/db/f7b98cdc3f81513fb25d3cbe2501d621882ee81150b745cdd1363278c10a/uritemplate-3.0.0.tar.gz";
      sha256 = "c02643cebe23fc8adb5e6becffe201185bf06c40bda5c0b4028a93f1527d011d";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.bsdOriginal;
      description = "URI templates";
    };
  };



  "urllib3" = python.mkDerivation {
    name = "urllib3-1.20";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/20/56/a6aa403b0998f857b474a538343ee483f5c02491bd1aebf61d42a3f60f77/urllib3-1.20.tar.gz";
      sha256 = "97ef2b6e2878d84c0126b9f4e608e37a951ca7848e4855a7f7f4437d5c34a72f";
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



  "whatthepatch" = python.mkDerivation {
    name = "whatthepatch-0.0.5";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/64/1e/7a63cba8a0d70245b9ab1c03694dabe36476fa65ee546e6dff6c8660434c/whatthepatch-0.0.5.tar.gz";
      sha256 = "494a2ec6c05b80f9ed1bd773f5ac9411298e1af6f0385f179840b5d60d001aa6";
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



  "yarl" = python.mkDerivation {
    name = "yarl-0.9.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/4a/15/a9f1b82bb88c2c11fee12d0e4248f0ed4cb0ec3e2b25fa4b0e52baff0899/yarl-0.9.2.tar.gz";
      sha256 = "4c63264bdf022e4ab509dd8946147dec026a4110c90e0a2dda9499385c312ece";
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



  "python-hglib" = python.mkDerivation {
    name = "python-hglib-2.3";
    src = pkgs.fetchurl { url = "https://pypi.python.org/packages/80/9c/1618281fc1ef0df4436b1435de6276452fefb46b111b3b00d3e20fcf5e17/python-hglib-2.3.tar.gz"; sha256 = "3d2e2eb2ecf73789635363784fdc6f0c0935256fe0263dfd6ed005a055c418df"; };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
    homepage = "";
      license = licenses.mit;
       description = "Mercurial Python library";
    };
  };

}