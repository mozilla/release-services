# generated using pypi2nix tool (version: 1.8.1)
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
            sed -i \
              -e "s|paths_to_remove.remove(auto_confirm)|#paths_to_remove.remove(auto_confirm)|"  \
              -e "s|self.uninstalled = paths_to_remove|#self.uninstalled = paths_to_remove|"  \
                $out/${pkgs.python35.sitePackages}/pip/req/req_install.py
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
          ln -s ${pythonPackages.python.interpreter} \
              $out/bin/${pythonPackages.python.executable}
          for dep in ${builtins.concatStringsSep " "
              (builtins.attrValues pkgs)}; do
            if [ -d "$dep/bin" ]; then
              for prog in "$dep/bin/"*; do
                if [ -x "$prog" ] && [ -f "$prog" ]; then
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
          ln -s ${pythonPackages.python.executable} \
              python3
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
        pythonPackages.buildPythonPackage (
          drv.drvAttrs // f drv.drvAttrs // { meta = drv.meta; }
        );
      withPackages = pkgs'':
        withPackages (pkgs // pkgs'');
    };

  python = withPackages {};

  generated = self: {
    "Logbook" = python.mkDerivation {
      name = "Logbook-1.2.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/3d/93/1862b5e453ec92d1068dd2613674d2291d622a3e56a0e250a8e4d88b39cc/Logbook-1.2.1.tar.gz"; sha256 = "ac201ccdb5b37170602a26d8a47df735e8904f11d51a73fa84f09a3014fc6001"; };
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
      name = "aiohttp-2.3.10";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/c0/b9/853b158f5cb5d218daaff0fb0dbc2bd7de45b2c6c5f563dff0ee530ec52a/aiohttp-2.3.10.tar.gz"; sha256 = "8adda6583ba438a4c70693374e10b60168663ffa6564c5c75d3c7a9055290964"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."async-timeout"
      self."chardet"
      self."idna-ssl"
      self."multidict"
      self."yarl"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/aio-libs/aiohttp/";
        license = licenses.asl20;
        description = "Async http client/server framework (asyncio)";
      };
    };

    "async-timeout" = python.mkDerivation {
      name = "async-timeout-1.4.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/6f/cc/ff80612164fe68bf97767052c5c783a033165df7d47a41ae5c1cc5ea480b/async-timeout-1.4.0.tar.gz"; sha256 = "983891535b1eca6ba82b9df671c8abff53c804fce3fa630058da5bbbda500340"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/aio-libs/async_timeout/";
        license = licenses.asl20;
        description = "Timeout context manager for asyncio programs";
      };
    };

    "attrs" = python.mkDerivation {
      name = "attrs-17.4.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/8b/0b/a06cfcb69d0cb004fde8bc6f0fd192d96d565d1b8aa2829f0f20adb796e5/attrs-17.4.0.tar.gz"; sha256 = "1c7960ccfd6a005cd9f7ba884e6316b5e430a3f1a6c37c5f87d8b43f83b54ec9"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."pytest"
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://www.attrs.org/";
        license = licenses.mit;
        description = "Classes Without Boilerplate";
      };
    };

    "awscli" = python.mkDerivation {
      name = "awscli-1.14.48";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/67/3c/837be8ec0e5a7dc5a87bdc8c139e1421b80b9749906a03ca8e14d350f8fb/awscli-1.14.48.tar.gz"; sha256 = "d81c6c85a477c90fa607ce07c98249ab70b04fa660135242003366f4be8f6472"; };
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
      name = "boto3-1.6.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/37/cd/d3fcdb481c6402123cd9dd19726ea89ffe9af0fc50b626fd6bf3a866ad71/boto3-1.6.1.tar.gz"; sha256 = "de924f18c50a496df7298ed462a2673613b384351599624b33175207722dc5bb"; };
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
      name = "botocore-1.9.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/3f/f4/331e9e7a19b0474061254d40bcdfa69435adbff03e42ea35a2fae13d5f29/botocore-1.9.1.tar.gz"; sha256 = "2a673d9289fc5d14b45fa904673d8f6d226ebfc238c0f354ac8d4e8955329152"; };
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

    "certifi" = python.mkDerivation {
      name = "certifi-2018.1.18";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/15/d4/2f888fc463d516ff7bf2379a4e9a552fef7f22a94147655d9b1097108248/certifi-2018.1.18.tar.gz"; sha256 = "edbc3f203427eef571f79a7692bb160a2b0f7ccaa31953e99bd17e307cf63f7d"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://certifi.io/";
        license = licenses.mpl20;
        description = "Python package for providing Mozilla's CA Bundle.";
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
      name = "decorator-4.2.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/70/f1/cb9373195639db13063f55eb06116310ad691e1fd125e6af057734dc44ea/decorator-4.2.1.tar.gz"; sha256 = "7d46dd9f3ea1cf5f06ee0e4e1277ae618cf48dfb10ada7c8427cd46c42702a0e"; };
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
      name = "docutils-0.14";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/84/f4/5771e41fdf52aabebbadecc9381d11dea0fa34e4759b4071244fa094804c/docutils-0.14.tar.gz"; sha256 = "51e64ef2ebfb29cae1faa133b3710143496eca21c530f3f71424d77687764274"; };
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
      name = "flake8-3.5.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/1e/ab/7730f6d6cdf73a3b7f98a2fe3b2cdf68e9e760a4a133e083607497d4c3a6/flake8-3.5.0.tar.gz"; sha256 = "7253265f7abd8b313e3892944044a365e3f4ac3fcdcfb4298f55ee9ddf188ba0"; };
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

    "idna" = python.mkDerivation {
      name = "idna-2.6";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/f4/bd/0467d62790828c23c47fc1dfa1b1f052b24efdf5290f071c7a91d0d82fd3/idna-2.6.tar.gz"; sha256 = "2c6a5de3089009e3da7c5dde64a141dbc8551d5b7f6cf4ed7c2568d0cc520a8f"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/kjd/idna";
        license = licenses.bsdOriginal;
        description = "Internationalized Domain Names in Applications (IDNA)";
      };
    };

    "idna-ssl" = python.mkDerivation {
      name = "idna-ssl-1.0.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/44/f4/97f7a58e814b3523a5e68bc8095c36cfa6daffb35f01b25248ec4605f53e/idna_ssl-1.0.0.tar.gz"; sha256 = "1227e44039bd31e02adaeafdbba61281596d623d222643fb021f87f2144ea147"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."idna"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/aio-libs/idna_ssl";
        license = licenses.mit;
        description = "Patch ssl.match_hostname for Unicode(idna) domains support";
      };
    };

    "ipdb" = python.mkDerivation {
      name = "ipdb-0.11";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/80/fe/4564de08f174f3846364b3add8426d14cebee228f741c27e702b2877e85b/ipdb-0.11.tar.gz"; sha256 = "7081c65ed7bfe7737f83fa4213ca8afd9617b42ff6b3f1daf9a3419839a2a00a"; };
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
      name = "ipython-6.2.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/fa/50/974211502bd72873728d44c3013fe79875c819c8fb69f778bcfd67bc7d38/ipython-6.2.1.tar.gz"; sha256 = "51c158a6c8b899898d1c91c6b51a34110196815cc905f9be0fa5878e19355608"; };
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
      name = "jedi-0.11.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/d2/41/430b325e411d564b1afc37bc7286c3549f4c415ada750a617fb1943c593d/jedi-0.11.1.tar.gz"; sha256 = "d6e799d04d1ade9459ed0f20de47c32f2285438956a677d083d3c98def59fa97"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."parso"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/davidhalter/jedi";
        license = licenses.mit;
        description = "An autocompletion tool for Python that can be used for text editors.";
      };
    };

    "jmespath" = python.mkDerivation {
      name = "jmespath-0.9.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/e5/21/795b7549397735e911b032f255cff5fb0de58f96da794274660bca4f58ef/jmespath-0.9.3.tar.gz"; sha256 = "6a81d4c9aa62caf061cb517b4d9ad1dd300374cd4706997aff9cd6aedd61fc64"; };
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
      src = pkgs.lib.cleanSource ./../cli_common;
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
      name = "multidict-4.1.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/ea/eb/c79ed6ff320ac8e935dcbff8a8833f1afb35c2433bff5bf1c9dabbd631b2/multidict-4.1.0.tar.gz"; sha256 = "fb4412490324705dcd2172baa8a3ea58ae23c5f982476805cad58ae929fe2a52"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/aio-libs/multidict/";
        license = licenses.asl20;
        description = "multidict implementation";
      };
    };

    "parso" = python.mkDerivation {
      name = "parso-0.1.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/14/3b/15cfd9c7a8bd9e3a2fe956e20fbc4e7c5768e06aea347d8eb68a05a71653/parso-0.1.1.tar.gz"; sha256 = "5815f3fe254e5665f3c5d6f54f086c2502035cb631a91341591b5a564203cffb"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/davidhalter/parso";
        license = licenses.mit;
        description = "A Python Parser";
      };
    };

    "pexpect" = python.mkDerivation {
      name = "pexpect-4.4.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/fa/c3/60c0cbf96f242d0b47a82e9ca634dcd6dcb043832cf05e17540812e1c707/pexpect-4.4.0.tar.gz"; sha256 = "67b85a1565968e3d5b5e7c9283caddc90c3947a2625bed1905be27bd5a03e47d"; };
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

    "pluggy" = python.mkDerivation {
      name = "pluggy-0.6.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/11/bf/cbeb8cdfaffa9f2ea154a30ae31a9d04a1209312e2919138b4171a1f8199/pluggy-0.6.0.tar.gz"; sha256 = "7f8ae7f5bdf75671a718d2daf0a64b7885f74510bcd98b1a0bb420eb9a9d0cff"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/pytest-dev/pluggy";
        license = licenses.mit;
        description = "plugin and hook calling mechanisms for python";
      };
    };

    "prompt-toolkit" = python.mkDerivation {
      name = "prompt-toolkit-1.0.15";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/8a/ad/cf6b128866e78ad6d7f1dc5b7f99885fb813393d9860778b2984582e81b5/prompt_toolkit-1.0.15.tar.gz"; sha256 = "858588f1983ca497f1cf4ffde01d978a3ea02b01c8a26a8bbc5cd2e66d816917"; };
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
      name = "ptyprocess-0.5.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/51/83/5d07dc35534640b06f9d9f1a1d2bc2513fb9cc7595a1b0e28ae5477056ce/ptyprocess-0.5.2.tar.gz"; sha256 = "e64193f0047ad603b71f202332ab5527c5e52aa7c8b609704fc28c0dc20c4365"; };
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
      name = "py-1.5.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/90/e3/e075127d39d35f09a500ebb4a90afd10f9ef0a1d28a6d09abeec0e444fdd/py-1.5.2.tar.gz"; sha256 = "ca18943e28235417756316bfada6cd96b23ce60dd532642690dcfdaba988a76d"; };
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
      name = "pyasn1-0.4.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/eb/3d/b7d0fdf4a882e26674c68c20f40682491377c4db1439870f5b6f862f76ed/pyasn1-0.4.2.tar.gz"; sha256 = "d258b0a71994f7770599835249cece1caef3c70def868c4915e6e5ca49b67d15"; };
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
      name = "pyflakes-1.6.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/26/85/f6a315cd3c1aa597fb3a04cc7d7dbea5b3cc66ea6bd13dfa0478bf4876e6/pyflakes-1.6.0.tar.gz"; sha256 = "8d616a382f243dbf19b54743f280b80198be0bca3a5396f1d2e1fca6223e8805"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/PyCQA/pyflakes";
        license = licenses.mit;
        description = "passive checker of Python programs";
      };
    };

    "pytest" = python.mkDerivation {
      name = "pytest-3.4.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/84/11/a6fe751118861b4d6587e07633f2e055733fc3678f7e5d7ae30303d90b7e/pytest-3.4.1.tar.gz"; sha256 = "9ddcb879c8cc859d2540204b5399011f842e5e8823674bf429f70ada281b3cc6"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."attrs"
      self."colorama"
      self."pluggy"
      self."py"
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://pytest.org";
        license = licenses.mit;
        description = "pytest: simple powerful testing with Python";
      };
    };

    "python-dateutil" = python.mkDerivation {
      name = "python-dateutil-2.6.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/54/bb/f1db86504f7a49e1d9b9301531181b00a1c7325dc85a29160ee3eaa73a54/python-dateutil-2.6.1.tar.gz"; sha256 = "891c38b2a02f5bb1be3e4793866c8df49c7d19baabf9c1bad62547e0b4866aca"; };
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
      name = "python-hglib-2.5";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/5a/c8/b8c95d3ee5d57c7961d918c16a09ebb8b3122a87e373bbda9f1f35769ff3/python-hglib-2.5.tar.gz"; sha256 = "fee180bb6796e5d2d25158b2d3c9f048648e427dd28b23a58d369adb14dd67cb"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://www.mercurial-scm.org/wiki/PythonHglibs";
        license = licenses.mit;
        description = "Mercurial Python library";
      };
    };

    "pytz" = python.mkDerivation {
      name = "pytz-2018.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/1b/50/4cdc62fc0753595fc16c8f722a89740f487c6e5670c644eb8983946777be/pytz-2018.3.tar.gz"; sha256 = "410bcd1d6409026fbaa65d9ed33bf6dd8b1e94a499e32168acfc7b332e4095c0"; };
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
      name = "requests-2.18.4";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/b0/e1/eab4fc3752e3d240468a8c0b284607899d2fbfb236a56b7377a329aa8d09/requests-2.18.4.tar.gz"; sha256 = "9c443e7324ba5b85070c4a818ade28bfabedf16ea10206da1132edaa6dda237e"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."certifi"
      self."chardet"
      self."idna"
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

    "s3transfer" = python.mkDerivation {
      name = "s3transfer-0.1.13";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/9a/66/c6a5ae4dbbaf253bd662921b805e4972451a6d214d0dc9fb3300cb642320/s3transfer-0.1.13.tar.gz"; sha256 = "90dc18e028989c609146e241ea153250be451e05ecc0c2832565231dacdf59c1"; };
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
        license = licenses.zpl21;
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
      name = "structlog-18.1.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/2a/ba/de51bd39a473d6dc6dd98689d1e31cf2df24d16f7c09911bae895ed27f12/structlog-18.1.0.tar.gz"; sha256 = "ff1e7aae015b346060c03b1cc4a1f29d428de7d858eaf06ea93ee35ac51071a0"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."colorama"
      self."pytest"
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://www.structlog.org/";
        license = licenses.mit;
        description = "Structured Logging for Python";
      };
    };

    "taskcluster" = python.mkDerivation {
      name = "taskcluster-2.1.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/9e/c6/a94dc47135d7516f6bf1b877079a08ffa4a420d5be2c39c2fa3d78f28875/taskcluster-2.1.3.tar.gz"; sha256 = "5bc6be5d59bd9a199b445db650081b9a8b7a8f436667172f9623bb34aff97556"; };
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

    "urllib3" = python.mkDerivation {
      name = "urllib3-1.22";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/ee/11/7c59620aceedcc1ef65e156cc5ce5a24ef87be4107c2b74458464e437a5d/urllib3-1.22.tar.gz"; sha256 = "cc44da8e1145637334317feebd728bd869a35285b93cbb4cca2577da7e62db4f"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."certifi"
      self."idna"
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

    "yarl" = python.mkDerivation {
      name = "yarl-1.1.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/91/14/5983db75b143681058d31a0a89a770f40a7f68f9b94cfeb6e6495b0039bf/yarl-1.1.1.tar.gz"; sha256 = "a69dd7e262cdb265ac7d5e929d55f2f3d07baaadd158c8f19caebf8dde08dfe8"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."idna"
      self."multidict"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/aio-libs/yarl/";
        license = licenses.asl20;
        description = "Yet another URL library";
      };
    };
  };
  localOverridesFile = ./requirements_override.nix;
  overrides = import localOverridesFile { inherit pkgs python; };
  commonOverrides = [
    
  ];
  allOverrides =
    (if (builtins.pathExists localOverridesFile)
     then [overrides] else [] ) ++ commonOverrides;

in python.withPackages
   (fix' (pkgs.lib.fold
            extends
            generated
            allOverrides
         )
   )