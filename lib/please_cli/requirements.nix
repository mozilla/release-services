# generated using pypi2nix tool (version: 1.8.0)
# See more at: https://github.com/garbas/pypi2nix
#
# COMMAND:
#   pypi2nix -v -V 3.5 -r requirements.txt -r requirements-dev.txt
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

  commonBuildInputs = [];
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



    "PyYAML" = python.mkDerivation {
      name = "PyYAML-3.12";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/4a/85/db5a2df477072b2902b0eb892feb37d88ac635d36245a72a6a69b23b383a/PyYAML-3.12.tar.gz"; sha256 = "592766c6303207a20efc445587778322d7f73b161bd994f227adaa341ba212ab"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://pyyaml.org/wiki/PyYAML";
        license = licenses.mit;
        description = "YAML parser and emitter for Python";
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



    "aioamqp" = python.mkDerivation {
      name = "aioamqp-0.10.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/22/f2/2b78c982e81eb840de18a419aa5c7d10519ccd81852e91310ebcbcd3e78b/aioamqp-0.10.0.tar.gz"; sha256 = "c618af6d005942a2a8711f7548348f9028fac2673f0dc2d192310cef83486204"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/polyconseil/aioamqp";
        license = licenses.bsdOriginal;
        description = "AMQP implementation using asyncio";
      };
    };



    "aiohttp" = python.mkDerivation {
      name = "aiohttp-2.0.7";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/f1/1a/e6090179b3c272c6e437cc6e0d78be6220727a7bdc9ee74bef214144c5d3/aiohttp-2.0.7.tar.gz"; sha256 = "76bfd47ee7fbda115cff486c3944fcb237ecbf6195bf2943fae74052fb40c4fe"; };
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



    "appdirs" = python.mkDerivation {
      name = "appdirs-1.4.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/48/69/d87c60746b393309ca30761f8e2b49473d43450b150cb08f3c6df5c11be5/appdirs-1.4.3.tar.gz"; sha256 = "9e5896d1372858f8dd3344faf4e5014d21849c756c8d5701f78f8a103b372d92"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/ActiveState/appdirs";
        license = licenses.mit;
        description = "A small Python module for determining appropriate platform-specific dirs, e.g. a \"user data dir\".";
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



    "awscli" = python.mkDerivation {
      name = "awscli-1.11.85";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/92/42/80428c6335515d064be63111f371ad32798ef28dea6d7beb2933b32c88c4/awscli-1.11.85.tar.gz"; sha256 = "9ff9a8608af18b0633b23301a1730b04a0b1e2940efc0e06891dd83662a8bd66"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."PyYAML"
      self."botocore"
      self."colorama"
      self."docutils"
      self."rsa"
      self."s3transfer"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://aws.amazon.com/cli/";
        license = licenses.asl20;
        description = "Universal Command Line Environment for AWS.";
      };
    };



    "boto3" = python.mkDerivation {
      name = "boto3-1.4.4";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/58/61/50d2e459049c5dbc963473a71fae928ac0e58ffe3fe7afd24c817ee210b9/boto3-1.4.4.tar.gz"; sha256 = "518f724c4758e5a5bed114fbcbd1cf470a15306d416ff421a025b76f1d390939"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."botocore"
      self."jmespath"
      self."s3transfer"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/boto/boto3";
        license = licenses.asl20;
        description = "The AWS SDK for Python";
      };
    };



    "botocore" = python.mkDerivation {
      name = "botocore-1.5.48";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/92/c9/1514d45766b64be0bbab2d895b17d849ca833eec1c4a07fb3e15bc425566/botocore-1.5.48.tar.gz"; sha256 = "56015c83e03241a536a14fec9ffb3a533eb7255a169c0ea6ca3e9ba5399a44b2"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."docutils"
      self."jmespath"
      self."python-dateutil"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/boto/botocore";
        license = licenses.asl20;
        description = "Low-level, data-driven core of boto 3.";
      };
    };



    "chardet" = python.mkDerivation {
      name = "chardet-3.0.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/91/05/28f23094cdf1410fb03533f0d71e6b4aad3c504100e83b8cea6fc899552c/chardet-3.0.2.tar.gz"; sha256 = "4f7832e7c583348a9eddd927ee8514b3bf717c061f57b21dbe7697211454d9bb"; };
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



    "click-spinner" = python.mkDerivation {
      name = "click-spinner-0.1.7";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/26/54/3fa581d2c510386b7a2e22bdd6cc8978ba0ee83fb2762c238cc7ac382f96/click-spinner-0.1.7.tar.gz"; sha256 = "a0703b4a21a1ba377716c5c768928b6c7575c087af926d3d586818426982ea30"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."click"
      self."pytest"
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/click-contrib/click-spinner";
        license = licenses.mit;
        description = "Spinner for Click";
      };
    };



    "colorama" = python.mkDerivation {
      name = "colorama-0.3.7";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/f0/d0/21c6449df0ca9da74859edc40208b3a57df9aca7323118c913e58d442030/colorama-0.3.7.tar.gz"; sha256 = "e043c8d32527607223652021ff648fbb394d5e19cba9f1a698670b338c9d782b"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/tartley/colorama";
        license = licenses.bsdOriginal;
        description = "Cross-platform colored terminal text.";
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



    "docutils" = python.mkDerivation {
      name = "docutils-0.13.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/05/25/7b5484aca5d46915493f1fd4ecb63c38c333bd32aa9ad6e19da8d08895ae/docutils-0.13.1.tar.gz"; sha256 = "718c0f5fb677be0f34b781e04241c4067cbd9327b66bdd8e763201130f5175be"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://docutils.sourceforge.net/";
        license = licenses.publicDomain;
        description = "Docutils -- Python Documentation Utilities";
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
      name = "ipython-6.0.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/75/03/bb1ce0cf9f8a86f52b34090708e1806bc11e2d29b193e7d6fe0afe9a61e5/ipython-6.0.0.tar.gz"; sha256 = "f429b82b8d9807068da734b15965768bd21b15d0b706340b6d1b4d6f6f5b98a4"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Pygments"
      self."colorama"
      self."decorator"
      self."jedi"
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



    "jmespath" = python.mkDerivation {
      name = "jmespath-0.9.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/96/6e/0723cccec195a37de6a428ad8879fe063b6debe5c855444e9285b27d253e/jmespath-0.9.2.tar.gz"; sha256 = "54c441e2e08b23f12d7fa7d8e6761768c47c969e6aed10eead57505ba760aee9"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/jmespath/jmespath.py";
        license = licenses.mit;
        description = "JSON Matching Expressions";
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



    "mozdef-client" = python.mkDerivation {
      name = "mozdef-client-1.0.11";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/cd/9b/d783ba277e2120add2709e45db926f8e916c5933df2db9725b7787884ae5/mozdef_client-1.0.11.tar.gz"; sha256 = "86b8c7065c21ce07d3095b5772f70fa152fe97258cde22311e5db4e34f5be26d"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."boto3"
      self."pytz"
      self."requests-futures"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/gdestuynder/mozdef_client";
        license = licenses.mpl20;
        description = "A client library to send messages/events using MozDef";
      };
    };



    "mozilla-cli-common" = python.mkDerivation {
      name = "mozilla-cli-common-1.0.0";
      src = ./../cli_common;
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Logbook"
      self."aioamqp"
      self."click"
      self."python-hglib"
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
      name = "multidict-2.1.4";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/2a/df/eaea73e46a58fd780c35ecc304ca42364fa3c1f4cd03568ed33b9d2c7547/multidict-2.1.4.tar.gz"; sha256 = "a77aa8c9f68846c3b5db43ff8ed2a7a884dbe845d01f55113a3fba78518c4cd7"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/aio-libs/multidict/";
        license = licenses.asl20;
        description = "multidict implementation";
      };
    };



    "packaging" = python.mkDerivation {
      name = "packaging-16.8";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/c6/70/bb32913de251017e266c5114d0a645f262fb10ebc9bf6de894966d124e35/packaging-16.8.tar.gz"; sha256 = "5d50835fdf0a7edf0b55e311b7c887786504efea1177abd7e69329a8e5ea619e"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."pyparsing"
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/pypa/packaging";
        license = licenses.bsdOriginal;
        description = "Core utilities for Python packages";
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



    "push" = python.mkDerivation {
      name = "push-0.0.1";
      src = pkgs.fetchurl { url = "https://github.com/garbas/push/archive/9883706635f1b145bff93d6490b2d9c270d3f674.zip"; sha256 = "fcb1db8b37a623ea452b2542e041c265f0677777e447c1c67bb63e04bfba78a9"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."requests"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/matejc/push";
        license = "";
        description = "Utility to push tar.gz docker images to v2 registry";
      };
    };



    "py" = python.mkDerivation {
      name = "py-1.4.33";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/2a/a5/139ca93a9ffffd9fc1d3f14be375af3085f53cc490c508cf1c988b886baa/py-1.4.33.tar.gz"; sha256 = "1f9a981438f2acc20470b301a07a496375641f902320f70e31916fe3377385a9"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://py.readthedocs.io/";
        license = licenses.mit;
        description = "library with cross-python path, ini-parsing, io, code, log facilities";
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
      name = "pytest-3.0.7";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/00/e9/f77dcd80bdb2e52760f38dbd904016da018ab4373898945da744e5e892e9/pytest-3.0.7.tar.gz"; sha256 = "b70696ebd1a5e6b627e7e3ac1365a4bc60aaf3495e843c1e70448966c5224cab"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."colorama"
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



    "requests" = python.mkDerivation {
      name = "requests-2.14.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/72/46/4abc3f5aaf7bf16a52206bb0c68677a26c216c1e6625c78c5aef695b5359/requests-2.14.2.tar.gz"; sha256 = "a274abba399a23e8713ffd2b5706535ae280ebe2b8069ee6a941cb089440d153"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
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



    "s3transfer" = python.mkDerivation {
      name = "s3transfer-0.1.10";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/8b/13/517e8ec7c13f0bb002be33fbf53c4e3198c55bb03148827d72064426fe6e/s3transfer-0.1.10.tar.gz"; sha256 = "ba1a9104939b7c0331dc4dd234d79afeed8b66edce77bbeeecd4f56de74a0fc1"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."botocore"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/boto/s3transfer";
        license = licenses.asl20;
        description = "An Amazon S3 Transfer Manager";
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
      name = "structlog-17.1.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/60/c9/5871c38001829eeb9c0f4f1e4da094cd5d7244107bbec8190a0333711103/structlog-17.1.0.tar.gz"; sha256 = "5c8bd391e269ea4e670cd0463bae88e0c2ff1d10c23adbe1d01c21662ce4c240"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."colorama"
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://www.structlog.org/";
        license = licenses.mit;
        description = "Structured Logging for Python";
      };
    };



    "taskcluster" = python.mkDerivation {
      name = "taskcluster-1.3.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/60/5f/2923a1f6ddb7cf96eb9da699ef4bb0e90b4f2c1dfb1a30d734f5ff6107b2/taskcluster-1.3.0.tar.gz"; sha256 = "e790fac22da8c7d981e1ce869fd27934a4eb1c38f4c8856706f2f33bd9fd4184"; };
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