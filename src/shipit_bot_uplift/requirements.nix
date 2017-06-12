# generated using pypi2nix tool (version: 1.8.0)
# See more at: https://github.com/garbas/pypi2nix
#
# COMMAND:
#   pypi2nix -v -V 3.5 -E libffi openssl pkgconfig freetype.dev -r requirements.txt -r requirements-dev.txt
#

{ pkgs ? import <nixpkgs> {}
}:

let

  inherit (pkgs) makeWrapper;
  inherit (pkgs.stdenv.lib) fix' extends inNixShell;

  pythonPackages =
  import "${toString pkgs.path}/pkgs/top-level/python-packages.nix" {
    inherit pkgs;
    inherit (pkgs) stdenv;
    python = pkgs.python35;
    # patching pip so it does not try to remove files when running nix-shell
    overrides =
      self: super: {
        bootstrapped-pip = super.bootstrapped-pip.overrideDerivation (old: {
          patchPhase = old.patchPhase + ''
            sed -i               -e "s|paths_to_remove.remove(auto_confirm)|#paths_to_remove.remove(auto_confirm)|"                -e "s|self.uninstalled = paths_to_remove|#self.uninstalled = paths_to_remove|"                  $out/${pkgs.python35.sitePackages}/pip/req/req_install.py
          '';
        });
      };
  };

  commonBuildInputs = with pkgs; [ libffi openssl pkgconfig freetype.dev ];
  commonDoCheck = false;

  withPackages = pkgs':
    let
      pkgs = builtins.removeAttrs pkgs' ["__unfix__"];
      interpreter = pythonPackages.buildPythonPackage {
        name = "python35-interpreter";
        buildInputs = [ makeWrapper ] ++ (builtins.attrValues pkgs);
        buildCommand = ''
          mkdir -p $out/bin
          ln -s ${pythonPackages.python.interpreter}               $out/bin/${pythonPackages.python.executable}
          for dep in ${builtins.concatStringsSep " "               (builtins.attrValues pkgs)}; do
            if [ -d "$dep/bin" ]; then
              for prog in "$dep/bin/"*; do
                if [ -f $prog ]; then
                  ln -s $prog $out/bin/`basename $prog`
                fi
              done
            fi
          done
          for prog in "$out/bin/"*; do
            wrapProgram "$prog" --prefix PYTHONPATH : "$PYTHONPATH"
          done
          pushd $out/bin
          ln -s ${pythonPackages.python.executable} python
          popd
        '';
        passthru.interpreter = pythonPackages.python;
      };
    in {
      __old = pythonPackages;
      inherit interpreter;
      mkDerivation = pythonPackages.buildPythonPackage;
      packages = pkgs;
      overrideDerivation = drv: f:
        pythonPackages.buildPythonPackage (drv.drvAttrs // f drv.drvAttrs);
      withPackages = pkgs'':
        withPackages (pkgs // pkgs'');
    };

  python = withPackages {};

  generated = self: {

    "Logbook" = python.mkDerivation {
      name = "Logbook-1.0.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/34/e8/6419c217bbf464fe8a902418120cccaf476201bd03b50958db24d6e90f65/Logbook-1.0.0.tar.gz"; sha256 = "87da2515a6b3db866283cb9d4e5a6ec44e52a1d556ebb2ea3b6e7e704b5f1872"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."pytest"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://logbook.pocoo.org/";
        license = licenses.bsdOriginal;
        description = "A logging replacement for Python";
      };
    };



    "Pygments" = python.mkDerivation {
      name = "Pygments-2.2.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/71/2a/2e4e77803a8bd6408a2903340ac498cb0a2181811af7c9ec92cb70b0308a/Pygments-2.2.0.tar.gz"; sha256 = "dbae1046def0efb574852fab9e90209b23f556367b5a320c0bcb871c77c3e8cc"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://pygments.org/";
        license = licenses.bsdOriginal;
        description = "Pygments is a syntax highlighting package written in Python.";
      };
    };



    "aiohttp" = python.mkDerivation {
      name = "aiohttp-2.1.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/cf/4a/bec3705f07294d9a4057fe5abd93ca89f52149931301674e1e6a9dd66366/aiohttp-2.1.0.tar.gz"; sha256 = "3e80d944e9295b1360e422d89746b99e23a99118420f826f990a632d284e21df"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."async-timeout"
      self."chardet"
      self."multidict"
      self."yarl"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/aio-libs/aiohttp/";
        license = licenses.asl20;
        description = "Async http client/server framework (asyncio)";
      };
    };



    "asn1crypto" = python.mkDerivation {
      name = "asn1crypto-0.22.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/67/14/5d66588868c4304f804ebaff9397255f6ec5559e46724c2496e0f26e68d6/asn1crypto-0.22.0.tar.gz"; sha256 = "cbbadd640d3165ab24b06ef25d1dca09a3441611ac15f6a6b452474fdf0aed1a"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/wbond/asn1crypto";
        license = licenses.mit;
        description = "Fast ASN.1 parser and serializer with definitions for private keys, public keys, certificates, CRL, OCSP, CMS, PKCS#3, PKCS#7, PKCS#8, PKCS#12, PKCS#5, X.509 and TSP";
      };
    };



    "async-timeout" = python.mkDerivation {
      name = "async-timeout-1.2.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/eb/a3/9fbe8bf7de4128d8f5562ca0b7b2f81d21b006085149528b937e1624e71f/async-timeout-1.2.1.tar.gz"; sha256 = "380e9bfd4c009a14931ffe487499b0906b00b3378bb743542cfd9fbb6d8e4657"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/aio-libs/async_timeout/";
        license = licenses.asl20;
        description = "Timeout context manager for asyncio programs";
      };
    };



    "certifi" = python.mkDerivation {
      name = "certifi-2017.4.17";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/dd/0e/1e3b58c861d40a9ca2d7ea4ccf47271d4456ae4294c5998ad817bd1b4396/certifi-2017.4.17.tar.gz"; sha256 = "f7527ebf7461582ce95f7a9e03dd141ce810d40590834f4ec20cddd54234c10a"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://certifi.io/";
        license = "ISC";
        description = "Python package for providing Mozilla's CA Bundle.";
      };
    };



    "cffi" = python.mkDerivation {
      name = "cffi-1.10.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/5b/b9/790f8eafcdab455bcd3bd908161f802c9ce5adbf702a83aa7712fcc345b7/cffi-1.10.0.tar.gz"; sha256 = "b3b02911eb1f6ada203b0763ba924234629b51586f72a21faacc638269f4ced5"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."pycparser"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://cffi.readthedocs.org";
        license = licenses.mit;
        description = "Foreign Function Interface for Python calling C code.";
      };
    };



    "chardet" = python.mkDerivation {
      name = "chardet-3.0.4";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/fc/bb/a5768c230f9ddb03acc9ef3f0d4a3cf93462473795d18e9535498c8f929d/chardet-3.0.4.tar.gz"; sha256 = "84ab92ed1c4d4f16916e05906b6b75a6c0fb5db821cc65e70cbd64a3e2a5eaae"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/chardet/chardet";
        license = licenses.lgpl2;
        description = "Universal encoding detector for Python 2 and 3";
      };
    };



    "click" = python.mkDerivation {
      name = "click-6.7";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/95/d9/c3336b6b5711c3ab9d1d3a80f1a3e2afeb9d8c02a7166462f6cc96570897/click-6.7.tar.gz"; sha256 = "f15516df478d5a56180fbf80e68f206010e6d160fc39fa508b65e035fd75130b"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/mitsuhiko/click";
        license = licenses.bsdOriginal;
        description = "A simple wrapper around optparse for powerful command line utilities.";
      };
    };



    "cryptography" = python.mkDerivation {
      name = "cryptography-1.9";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/2a/0c/31bd69469e90035381f0197b48bf71032991d9f07a7e444c311b4a23a3df/cryptography-1.9.tar.gz"; sha256 = "5518337022718029e367d982642f3e3523541e098ad671672a90b82474c84882"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."asn1crypto"
      self."cffi"
      self."flake8"
      self."idna"
      self."pytest"
      self."pytz"
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/pyca/cryptography";
        license = licenses.bsdOriginal;
        description = "cryptography is a package which provides cryptographic recipes and primitives to Python developers.";
      };
    };



    "cycler" = python.mkDerivation {
      name = "cycler-0.10.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/c2/4b/137dea450d6e1e3d474e1d873cd1d4f7d3beed7e0dc973b06e8e10d32488/cycler-0.10.0.tar.gz"; sha256 = "cd7b2d1018258d7247a71425e9f26463dfb444d411c39569972f4ce586b0c9d8"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/matplotlib/cycler";
        license = licenses.bsdOriginal;
        description = "Composable style cycles";
      };
    };



    "decorator" = python.mkDerivation {
      name = "decorator-4.0.11";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/cc/ac/5a16f1fc0506ff72fcc8fd4e858e3a1c231f224ab79bb7c4c9b2094cc570/decorator-4.0.11.tar.gz"; sha256 = "953d6bf082b100f43229cf547f4f97f97e970f5ad645ee7601d55ff87afdfe76"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/micheles/decorator";
        license = licenses.bsdOriginal;
        description = "Better living through Python with decorators";
      };
    };



    "elasticsearch" = python.mkDerivation {
      name = "elasticsearch-5.4.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/43/15/790c7b24cd3dcbbc7c09c7d595ee2ad2d9e430ff04921b540209bef1ea16/elasticsearch-5.4.0.tar.gz"; sha256 = "e754c688e20fe73160fb6f7f5b63f2a71c78788dc9e6908950681d3a39b56e85"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."requests"
      self."urllib3"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/elastic/elasticsearch-py";
        license = licenses.asl20;
        description = "Python client for Elasticsearch";
      };
    };



    "flake8" = python.mkDerivation {
      name = "flake8-3.3.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/47/64/382631de5fd8dab367bedeff6b5b55fd9a7c883daa44f4032636e2d203ca/flake8-3.3.0.tar.gz"; sha256 = "b907a26dcf5580753d8f80f1be0ec1d5c45b719f7bac441120793d1a70b03f12"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."mccabe"
      self."pycodestyle"
      self."pyflakes"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://gitlab.com/pycqa/flake8";
        license = licenses.mit;
        description = "the modular source code checker: pep8, pyflakes and co";
      };
    };



    "flake8-coding" = python.mkDerivation {
      name = "flake8-coding-1.3.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/ae/26/3c6304d646f8ee27d6c40bfcd9874fea870098c3ef3cf60e284ea9db29ef/flake8-coding-1.3.0.tar.gz"; sha256 = "ba01e96f879377766a3d71f3499a832b19386ce4831270bfe671ab57d0fe50be"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."flake8"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/tk0miya/flake8-coding";
        license = licenses.asl20;
        description = "Adds coding magic comment checks to flake8";
      };
    };



    "flake8-quotes" = python.mkDerivation {
      name = "flake8-quotes-0.11.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/d5/9b/20adf6a3c718a4ad48c1968e2851aa27b9cb9c907b96519fe7797bebef7f/flake8-quotes-0.11.0.tar.gz"; sha256 = "0b8e5ea5407e8308ff237ab814414a1dcd4c309c5c47363b6ad07a35068684e1"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."flake8"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/zheller/flake8-quotes/";
        license = licenses.mit;
        description = "Flake8 lint for quotes.";
      };
    };



    "google-api-python-client" = python.mkDerivation {
      name = "google-api-python-client-1.6.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/e8/04/4bb1672918e4fc6d6a8201bdaf986b9fb4763f2a47b11496186dbbbd40ce/google-api-python-client-1.6.2.tar.gz"; sha256 = "8c2f50f8057571a5f817c74820cadb754d47799c5a4ea463c1500fe8e092c1ae"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."httplib2"
      self."oauth2client"
      self."six"
      self."uritemplate"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/google/google-api-python-client/";
        license = licenses.asl20;
        description = "Google API Client Library for Python";
      };
    };



    "httplib2" = python.mkDerivation {
      name = "httplib2-0.10.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/e4/2e/a7e27d2c36076efeb8c0e519758968b20389adf57a9ce3af139891af2696/httplib2-0.10.3.tar.gz"; sha256 = "e404d3b7bd86c1bc931906098e7c1305d6a3a6dcef141b8bb1059903abb3ceeb"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/httplib2/httplib2";
        license = licenses.mit;
        description = "A comprehensive HTTP client library.";
      };
    };



    "icalendar" = python.mkDerivation {
      name = "icalendar-3.11.4";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/bb/6a/486b4a882d03042e569a40a4e17aebcb1d8d2b8f54620007adaba43c67af/icalendar-3.11.4.tar.gz"; sha256 = "5696b18f791bbbb5972b87ea3d3c42a855ae641b0608477a451aa23f7defa347"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."python-dateutil"
      self."pytz"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/collective/icalendar";
        license = licenses.bsdOriginal;
        description = "iCalendar parser/generator";
      };
    };



    "idna" = python.mkDerivation {
      name = "idna-2.5";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/d8/82/28a51052215014efc07feac7330ed758702fc0581347098a81699b5281cb/idna-2.5.tar.gz"; sha256 = "3cb5ce08046c4e3a560fc02f138d0ac63e00f8ce5901a56b32ec8b7994082aab"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/kjd/idna";
        license = licenses.bsdOriginal;
        description = "Internationalized Domain Names in Applications (IDNA)";
      };
    };



    "ipdb" = python.mkDerivation {
      name = "ipdb-0.10.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/ad/cc/0e7298e1fbf2efd52667c9354a12aa69fb6f796ce230cca03525051718ef/ipdb-0.10.3.tar.gz"; sha256 = "9ea256b4280fbe12840fb9dfc3ce498c6c6de03352eca293e4400b0dfbed2b28"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."ipython"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/gotcha/ipdb";
        license = licenses.bsdOriginal;
        description = "IPython-enabled pdb";
      };
    };



    "ipython" = python.mkDerivation {
      name = "ipython-6.1.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/79/63/b671fc2bf0051739e87a7478a207bbeb45cfae3c328d38ccdd063d9e0074/ipython-6.1.0.tar.gz"; sha256 = "5c53e8ee4d4bec27879982b9f3b4aa2d6e3cfd7b26782d250fa117f85bb29814"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Pygments"
      self."decorator"
      self."jedi"
      self."numpy"
      self."pexpect"
      self."pickleshare"
      self."prompt-toolkit"
      self."requests"
      self."simplegeneric"
      self."traitlets"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://ipython.org";
        license = licenses.bsdOriginal;
        description = "IPython: Productive Interactive Computing";
      };
    };



    "ipython-genutils" = python.mkDerivation {
      name = "ipython-genutils-0.2.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/e8/69/fbeffffc05236398ebfcfb512b6d2511c622871dca1746361006da310399/ipython_genutils-0.2.0.tar.gz"; sha256 = "eb2e116e75ecef9d4d228fdc66af54269afa26ab4463042e33785b887c628ba8"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://ipython.org";
        license = licenses.bsdOriginal;
        description = "Vestigial utilities from IPython";
      };
    };



    "jedi" = python.mkDerivation {
      name = "jedi-0.10.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/80/b9/4e9b0b999deeec8a91cb84e567380853a842e6c387c9d39b8fc9a49953fa/jedi-0.10.2.tar.gz"; sha256 = "7abb618cac6470ebbd142e59c23daec5e6e063bfcecc8a43a037d2ab57276f4e"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/davidhalter/jedi";
        license = licenses.mit;
        description = "An autocompletion tool for Python that can be used for text editors.";
      };
    };



    "libmozdata" = python.mkDerivation {
      name = "libmozdata-0.1.31";
      src = pkgs.fetchurl { url = "https://github.com/mozilla/libmozdata/archive/13644a4547d6782d7d54fb3e3ecb6111a183e7b6.tar.gz"; sha256 = "d885c09d913d50f1279e3029ccca1da64d240a9192174d8b7326ab4af17a04d0"; };
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
        homepage = "https://github.com/mozilla/libmozdata";
        license = "MPL2";
        description = "Library to access and aggregate several Mozilla data sources.";
      };
    };



    "matplotlib" = python.mkDerivation {
      name = "matplotlib-2.0.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/f5/f0/9da3ef24ea7eb0ccd12430a261b66eca36b924aeef06e17147f9f9d7d310/matplotlib-2.0.2.tar.gz"; sha256 = "0ffbc44faa34a8b1704bc108c451ecf87988f900ef7ce757b8e2e84383121ff1"; };
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
        homepage = "http://matplotlib.org";
        license = licenses.psfl;
        description = "Python plotting package";
      };
    };



    "mccabe" = python.mkDerivation {
      name = "mccabe-0.6.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/06/18/fa675aa501e11d6d6ca0ae73a101b2f3571a565e0f7d38e062eec18a91ee/mccabe-0.6.1.tar.gz"; sha256 = "dd8d182285a0fe56bace7f45b5e7d1a6ebcbf524e8f3bd87eb0f125271b8831f"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/pycqa/mccabe";
        license = licenses.mit;
        description = "McCabe checker, plugin for flake8";
      };
    };



    "mohawk" = python.mkDerivation {
      name = "mohawk-0.3.4";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/19/22/10f696548a8d41ad41b92ab6c848c60c669e18c8681c179265ce4d048b03/mohawk-0.3.4.tar.gz"; sha256 = "e98b331d9fa9ece7b8be26094cbe2d57613ae882133cc755167268a984bc0ab3"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/kumar303/mohawk";
        license = licenses.mpl20;
        description = "Library for Hawk HTTP authorization";
      };
    };



    "mozilla-cli-common" = python.mkDerivation {
      name = "mozilla-cli-common-1.0.0";
      src = ./../../lib/cli_common;
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Logbook"
      self."click"
      self."python-hglib"
      self."raven"
      self."structlog"
      self."taskcluster"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/mozilla-releng/services";
        license = "MPL2";
        description = "Services behind https://mozilla-releng.net";
      };
    };



    "multidict" = python.mkDerivation {
      name = "multidict-2.1.6";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/e5/04/b272ba67ed896c5e9ac05cac916da6508855352524aae00f99938bdf9dc6/multidict-2.1.6.tar.gz"; sha256 = "9ec33a1da4d2096949e29ddd66a352aae57fad6b5483087d54566a2f6345ae10"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/aio-libs/multidict/";
        license = licenses.asl20;
        description = "multidict implementation";
      };
    };



    "numpy" = python.mkDerivation {
      name = "numpy-1.13.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/05/84/0feb999c05f252af50a5fbc463268044feda92cdaad8cb0d0a6073d76057/numpy-1.13.0.zip"; sha256 = "dcff367b725586830ff0e20b805c7654c876c2d4585c0834a6049502b9d6cf7e"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://www.numpy.org";
        license = licenses.bsdOriginal;
        description = "NumPy: array processing for numbers, strings, records, and objects.";
      };
    };



    "oauth2client" = python.mkDerivation {
      name = "oauth2client-4.1.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/7f/60/d683b7933ae7f4d2f3cd53afda197025d7178ca1516aa340aba0020b1094/oauth2client-4.1.1.tar.gz"; sha256 = "fd02b705092b76f443028328eaed366135f26c0d3e52bdbf66e649a944938ca1"; };
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
        homepage = "http://github.com/google/oauth2client/";
        license = licenses.asl20;
        description = "OAuth 2.0 client library";
      };
    };



    "pexpect" = python.mkDerivation {
      name = "pexpect-4.2.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/e8/13/d0b0599099d6cd23663043a2a0bb7c61e58c6ba359b2656e6fb000ef5b98/pexpect-4.2.1.tar.gz"; sha256 = "3d132465a75b57aa818341c6521392a06cc660feb3988d7f1074f39bd23c9a92"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."ptyprocess"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://pexpect.readthedocs.io/";
        license = licenses.isc;
        description = "Pexpect allows easy control of interactive console applications.";
      };
    };



    "pickleshare" = python.mkDerivation {
      name = "pickleshare-0.7.4";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/69/fe/dd137d84daa0fd13a709e448138e310d9ea93070620c9db5454e234af525/pickleshare-0.7.4.tar.gz"; sha256 = "84a9257227dfdd6fe1b4be1319096c20eb85ff1e82c7932f36efccfe1b09737b"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/pickleshare/pickleshare";
        license = licenses.mit;
        description = "Tiny 'shelve'-like database with concurrency support";
      };
    };



    "prompt-toolkit" = python.mkDerivation {
      name = "prompt-toolkit-1.0.14";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/55/56/8c39509b614bda53e638b7500f12577d663ac1b868aef53426fc6a26c3f5/prompt_toolkit-1.0.14.tar.gz"; sha256 = "cc66413b1b4b17021675d9f2d15d57e640b06ddfd99bb724c73484126d22622f"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."six"
      self."wcwidth"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/jonathanslenders/python-prompt-toolkit";
        license = licenses.bsdOriginal;
        description = "Library for building powerful interactive command lines in Python";
      };
    };



    "ptyprocess" = python.mkDerivation {
      name = "ptyprocess-0.5.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/db/d7/b465161910f3d1cef593c5e002bff67e0384898f597f1a7fdc8db4c02bf6/ptyprocess-0.5.1.tar.gz"; sha256 = "0530ce63a9295bfae7bd06edc02b6aa935619f486f0f1dc0972f516265ee81a6"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/pexpect/ptyprocess";
        license = "";
        description = "Run a subprocess in a pseudo terminal";
      };
    };



    "py" = python.mkDerivation {
      name = "py-1.4.34";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/68/35/58572278f1c097b403879c1e9369069633d1cbad5239b9057944bb764782/py-1.4.34.tar.gz"; sha256 = "0f2d585d22050e90c7d293b6451c83db097df77871974d90efd5a30dc12fcde3"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://py.readthedocs.io/";
        license = licenses.mit;
        description = "library with cross-python path, ini-parsing, io, code, log facilities";
      };
    };



    "pyOpenSSL" = python.mkDerivation {
      name = "pyOpenSSL-17.0.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/9f/32/80fe4fddeb731b7766cd09fe0b2032a91b43dae655e216792af2a6ae3190/pyOpenSSL-17.0.0.tar.gz"; sha256 = "48abfe9d2bb8eb8d8947c8452b0223b7b1be2383b332f3b4f248fe59ef0bafdd"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."cryptography"
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://pyopenssl.readthedocs.io/";
        license = licenses.asl20;
        description = "Python wrapper module around the OpenSSL library";
      };
    };



    "pyasn1" = python.mkDerivation {
      name = "pyasn1-0.2.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/69/17/eec927b7604d2663fef82204578a0056e11e0fc08d485fdb3b6199d9b590/pyasn1-0.2.3.tar.gz"; sha256 = "738c4ebd88a718e700ee35c8d129acce2286542daa80a82823a7073644f706ad"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/etingof/pyasn1";
        license = licenses.bsdOriginal;
        description = "ASN.1 types and codecs";
      };
    };



    "pyasn1-modules" = python.mkDerivation {
      name = "pyasn1-modules-0.0.9";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/cf/57/d4097cea8caf360ffe0c5d6f25c2cb9317500cdc000fd02a741ba6e64c9e/pyasn1-modules-0.0.9.tar.gz"; sha256 = "be0e4157e4a53551279d6c6e366b080527f5fd068616835b4abf32c14f657f5f"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."pyasn1"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/etingof/pyasn1-modules";
        license = licenses.bsdOriginal;
        description = "A collection of ASN.1-based protocols modules.";
      };
    };



    "pycodestyle" = python.mkDerivation {
      name = "pycodestyle-2.3.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/e1/88/0e2cbf412bd849ea6f1af1f97882add46a374f4ba1d2aea39353609150ad/pycodestyle-2.3.1.tar.gz"; sha256 = "682256a5b318149ca0d2a9185d365d8864a768a28db66a84a2ea946bcc426766"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://pycodestyle.readthedocs.io/";
        license = licenses.mit;
        description = "Python style guide checker";
      };
    };



    "pycparser" = python.mkDerivation {
      name = "pycparser-2.17";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/be/64/1bb257ffb17d01f4a38d7ce686809a736837ad4371bcc5c42ba7a715c3ac/pycparser-2.17.tar.gz"; sha256 = "0aac31e917c24cb3357f5a4d5566f2cc91a19ca41862f6c3c22dc60a629673b6"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/eliben/pycparser";
        license = licenses.bsdOriginal;
        description = "C parser in Python";
      };
    };



    "pyflakes" = python.mkDerivation {
      name = "pyflakes-1.5.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/5b/b7/dcd6ebc826065ca4ccd2406aac4378e1df6eb91124625d45d520219932a1/pyflakes-1.5.0.tar.gz"; sha256 = "aa0d4dff45c0cc2214ba158d29280f8fa1129f3e87858ef825930845146337f4"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/PyCQA/pyflakes";
        license = licenses.mit;
        description = "passive checker of Python programs";
      };
    };



    "pyparsing" = python.mkDerivation {
      name = "pyparsing-2.2.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/3c/ec/a94f8cf7274ea60b5413df054f82a8980523efd712ec55a59e7c3357cf7c/pyparsing-2.2.0.tar.gz"; sha256 = "0832bcf47acd283788593e7a0f542407bd9550a55a8a8435214a1960e04bcb04"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://pyparsing.wikispaces.com/";
        license = licenses.mit;
        description = "Python parsing module";
      };
    };



    "pytest" = python.mkDerivation {
      name = "pytest-3.1.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/96/51/8fa6bdb9c80e21a90e162f6774da2506497ef0c92afae8ba654c3a5ce4c3/pytest-3.1.1.tar.gz"; sha256 = "0173a366a259e1d23b0f433b1f06e1b753110bb33e77a79bd8ea54cbd0b5df15"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."py"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://pytest.org";
        license = licenses.mit;
        description = "pytest: simple powerful testing with Python";
      };
    };



    "python-dateutil" = python.mkDerivation {
      name = "python-dateutil-2.6.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/51/fc/39a3fbde6864942e8bb24c93663734b74e281b984d1b8c4f95d64b0c21f6/python-dateutil-2.6.0.tar.gz"; sha256 = "62a2f8df3d66f878373fd0072eacf4ee52194ba302e00082828e0d263b0418d2"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://dateutil.readthedocs.io";
        license = licenses.bsdOriginal;
        description = "Extensions to the standard Python datetime module";
      };
    };



    "python-hglib" = python.mkDerivation {
      name = "python-hglib-2.4";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/3a/6c/52c4ba6050b80e266d87783ccd4d39b76a0d2459965abf1c7bde54dd9a72/python-hglib-2.4.tar.gz"; sha256 = "693d6ed92a6566e78802c7a03c256cda33d08c63ad3f00fcfa11379b184b9462"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://selenic.com/repo/python-hglib";
        license = licenses.mit;
        description = "Mercurial Python library";
      };
    };



    "pytz" = python.mkDerivation {
      name = "pytz-2017.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/a4/09/c47e57fc9c7062b4e83b075d418800d322caa87ec0ac21e6308bd3a2d519/pytz-2017.2.zip"; sha256 = "f5c056e8f62d45ba8215e5cb8f50dfccb198b4b9fbea8500674f3443e4689589"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://pythonhosted.org/pytz";
        license = licenses.mit;
        description = "World timezone definitions, modern and historical";
      };
    };



    "raven" = python.mkDerivation {
      name = "raven-6.1.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/ee/82/9a85650c174920f5bd260b8138a1db7190156e55193b0a1d03d2fa7a2811/raven-6.1.0.tar.gz"; sha256 = "02cabffb173b99d860a95d4908e8b1864aad1b8452146e13fd7e212aa576a884"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Logbook"
      self."flake8"
      self."pycodestyle"
      self."pytest"
      self."pytz"
      self."requests"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/getsentry/raven-python";
        license = licenses.bsdOriginal;
        description = "Raven is a client for Sentry (https://getsentry.com)";
      };
    };



    "requests" = python.mkDerivation {
      name = "requests-2.17.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/27/c7/a45641c83c6e28f4922ba6af3d4ae4d79b41932c2f3d77fed9e0bf878149/requests-2.17.3.tar.gz"; sha256 = "8d29f97ed1541709b57caddb77bb20592411d7ca10ec4f03275f49ee8456e225"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."certifi"
      self."chardet"
      self."cryptography"
      self."idna"
      self."pyOpenSSL"
      self."urllib3"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://python-requests.org";
        license = licenses.asl20;
        description = "Python HTTP for Humans.";
      };
    };



    "requests-futures" = python.mkDerivation {
      name = "requests-futures-0.9.7";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/2c/f0/d9a6d4472286405956dd5ac6279fe932a86151df9816bc35afe601495819/requests-futures-0.9.7.tar.gz"; sha256 = "a9ca2c3480b6fac29ec5de59c146742e2ab2b60f8c68581766094edb52ea7bad"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."requests"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/ross/requests-futures";
        license = "License :: OSI Approved :: Apache Software License";
        description = "Asynchronous Python HTTP for Humans.";
      };
    };



    "rsa" = python.mkDerivation {
      name = "rsa-3.4.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/14/89/adf8b72371e37f3ca69c6cb8ab6319d009c4a24b04a31399e5bd77d9bb57/rsa-3.4.2.tar.gz"; sha256 = "25df4e10c263fb88b5ace923dd84bf9aa7f5019687b5e55382ffcdb8bede9db5"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."pyasn1"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://stuvel.eu/rsa";
        license = "License :: OSI Approved :: Apache Software License";
        description = "Pure-Python RSA implementation";
      };
    };



    "simplegeneric" = python.mkDerivation {
      name = "simplegeneric-0.8.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/3d/57/4d9c9e3ae9a255cd4e1106bb57e24056d3d0709fc01b2e3e345898e49d5b/simplegeneric-0.8.1.zip"; sha256 = "dc972e06094b9af5b855b3df4a646395e43d1c9d0d39ed345b7393560d0b9173"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://cheeseshop.python.org/pypi/simplegeneric";
        license = licenses.zpt21;
        description = "Simple generic functions (similar to Python's own len(), pickle.dump(), etc.)";
      };
    };



    "six" = python.mkDerivation {
      name = "six-1.10.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/b3/b2/238e2590826bfdd113244a40d9d3eb26918bd798fc187e2360a8367068db/six-1.10.0.tar.gz"; sha256 = "105f8d68616f8248e24bf0e9372ef04d3cc10104f1980f54d57b2ce73a5ad56a"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://pypi.python.org/pypi/six/";
        license = licenses.mit;
        description = "Python 2 and 3 compatibility utilities";
      };
    };



    "slugid" = python.mkDerivation {
      name = "slugid-1.0.7";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/dd/96/b05c6d357f8d6932bea2b360537360517d1154b82cc71b8eccb70b28bdde/slugid-1.0.7.tar.gz"; sha256 = "6dab3c7eef0bb423fb54cb7752e0f466ddd0ee495b78b763be60e8a27f69e779"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://taskcluster.github.io/slugid.py";
        license = licenses.mpl20;
        description = "Base64 encoded uuid v4 slugs";
      };
    };



    "structlog" = python.mkDerivation {
      name = "structlog-17.2.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/8f/b1/d86780fdcddb3ff3326392b4226d54c109592d5456f395ca5eb2350d7fbc/structlog-17.2.0.tar.gz"; sha256 = "6980001045abd235fa12582222627c19b89109e58b85eb77d5a5abc778df6e20"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://www.structlog.org/";
        license = licenses.mit;
        description = "Structured Logging for Python";
      };
    };



    "taskcluster" = python.mkDerivation {
      name = "taskcluster-1.3.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/d6/22/965885edd7bac853f0eab17150cb4b6e605e89601452ba62504421b8f05b/taskcluster-1.3.3.tar.gz"; sha256 = "8874b556fe0cd815c5cf9509f263a323b0ab91a680edfe9afdab04ca65ff1375"; };
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
        homepage = "https://github.com/taskcluster/taskcluster-client.py";
        license = "";
        description = "Python client for Taskcluster";
      };
    };



    "traitlets" = python.mkDerivation {
      name = "traitlets-4.3.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/a5/98/7f5ef2fe9e9e071813aaf9cb91d1a732e0a68b6c44a32b38cb8e14c3f069/traitlets-4.3.2.tar.gz"; sha256 = "9c4bd2d267b7153df9152698efb1050a5d84982d3384a37b2c1f7723ba3e7835"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."decorator"
      self."ipython-genutils"
      self."pytest"
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://ipython.org";
        license = licenses.bsdOriginal;
        description = "Traitlets Python config system";
      };
    };



    "uritemplate" = python.mkDerivation {
      name = "uritemplate-3.0.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/cd/db/f7b98cdc3f81513fb25d3cbe2501d621882ee81150b745cdd1363278c10a/uritemplate-3.0.0.tar.gz"; sha256 = "c02643cebe23fc8adb5e6becffe201185bf06c40bda5c0b4028a93f1527d011d"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://uritemplate.readthedocs.org";
        license = licenses.bsdOriginal;
        description = "URI templates";
      };
    };



    "urllib3" = python.mkDerivation {
      name = "urllib3-1.21.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/96/d9/40e4e515d3e17ed0adbbde1078e8518f8c4e3628496b56eb8f026a02b9e4/urllib3-1.21.1.tar.gz"; sha256 = "b14486978518ca0901a76ba973d7821047409d7f726f22156b24e83fd71382a5"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."certifi"
      self."cryptography"
      self."idna"
      self."pyOpenSSL"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://urllib3.readthedocs.io/";
        license = licenses.mit;
        description = "HTTP library with thread-safe connection pooling, file post, and more.";
      };
    };



    "wcwidth" = python.mkDerivation {
      name = "wcwidth-0.1.7";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/55/11/e4a2bb08bb450fdbd42cc709dd40de4ed2c472cf0ccb9e64af22279c5495/wcwidth-0.1.7.tar.gz"; sha256 = "3df37372226d6e63e1b1e1eda15c594bca98a22d33a23832a90998faa96bc65e"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/jquast/wcwidth";
        license = licenses.mit;
        description = "Measures number of Terminal column cells of wide-character codes";
      };
    };



    "whatthepatch" = python.mkDerivation {
      name = "whatthepatch-0.0.5";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/64/1e/7a63cba8a0d70245b9ab1c03694dabe36476fa65ee546e6dff6c8660434c/whatthepatch-0.0.5.tar.gz"; sha256 = "494a2ec6c05b80f9ed1bd773f5ac9411298e1af6f0385f179840b5d60d001aa6"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/cscorley/whatthepatch";
        license = licenses.mit;
        description = "A patch parsing library.";
      };
    };



    "yarl" = python.mkDerivation {
      name = "yarl-0.10.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/83/cd/c9d2c92f12de6bbb8ab025a6a9488d64e75f8650e52232b4718124d28279/yarl-0.10.2.tar.gz"; sha256 = "a042c5b3584531cd09cd5ca647f71553df7caaa3359b9b3f7eb34c3b1045b38d"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."multidict"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/aio-libs/yarl/";
        license = licenses.asl20;
        description = "Yet another URL library";
      };
    };

  };
  overrides = import ./requirements_override.nix { inherit pkgs python; };
  commonOverrides = [

  ];

in python.withPackages
   (fix' (pkgs.lib.fold
            extends
            generated
            ([overrides] ++ commonOverrides)
         )
   )