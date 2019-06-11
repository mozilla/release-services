# generated using pypi2nix tool (version: 2.0.0)
# See more at: https://github.com/garbas/pypi2nix
#
# COMMAND:
#   pypi2nix -v -C /tmp/release-services-jgax257b/src/docs/../../../tmp/pypi2nix -V 3.7 -O ../../nix/requirements_override.nix -E pkgconfig -E zlib -E libjpeg -E openjpeg -E libtiff -E freetype -E lcms2 -E libwebp -E tcl -r requirements.txt
#

{ pkgs ? import <nixpkgs> {},
  overrides ? ({ pkgs, python }: self: super: {})
}:

let

  inherit (pkgs) makeWrapper;
  inherit (pkgs.stdenv.lib) fix' extends inNixShell;

  pythonPackages =
  import "${toString pkgs.path}/pkgs/top-level/python-packages.nix" {
    inherit pkgs;
    inherit (pkgs) stdenv;
    python = pkgs.python37;
    # patching pip so it does not try to remove files when running nix-shell
    overrides =
      self: super: {
        bootstrapped-pip = super.bootstrapped-pip.overrideDerivation (old: {
          patchPhase = old.patchPhase + ''
            if [ -e $out/${pkgs.python37.sitePackages}/pip/req/req_install.py ]; then
              sed -i \
                -e "s|paths_to_remove.remove(auto_confirm)|#paths_to_remove.remove(auto_confirm)|"  \
                -e "s|self.uninstalled = paths_to_remove|#self.uninstalled = paths_to_remove|"  \
                $out/${pkgs.python37.sitePackages}/pip/req/req_install.py
            fi
          '';
        });
      };
  };

  commonBuildInputs = with pkgs; [ pkgconfig zlib libjpeg openjpeg libtiff freetype lcms2 libwebp tcl ];
  commonDoCheck = false;

  withPackages = pkgs':
    let
      pkgs = builtins.removeAttrs pkgs' ["__unfix__"];
      interpreterWithPackages = selectPkgsFn: pythonPackages.buildPythonPackage {
        name = "python37-interpreter";
        buildInputs = [ makeWrapper ] ++ (selectPkgsFn pkgs);
        buildCommand = ''
          mkdir -p $out/bin
          ln -s ${pythonPackages.python.interpreter} \
              $out/bin/${pythonPackages.python.executable}
          for dep in ${builtins.concatStringsSep " "
              (selectPkgsFn pkgs)}; do
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

      interpreter = interpreterWithPackages builtins.attrValues;
    in {
      __old = pythonPackages;
      inherit interpreter;
      inherit interpreterWithPackages;
      mkDerivation = args: pythonPackages.buildPythonPackage (args // { nativeBuildInputs = args.buildInputs; });
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
    "Babel" = python.mkDerivation {
      name = "Babel-2.7.0";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/bd/78/9fb975cbb3f4b136de2cd4b5e5ce4a3341169ebf4c6c03630996d05428f1/Babel-2.7.0.tar.gz";
        sha256 = "e86135ae101e31e2c8ec20a4e0c5220f4eed12487d5cf3f78be7e98d3a57fc28";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [
        self."pytz"
      ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://babel.pocoo.org/";
        license = licenses.bsdOriginal;
        description = "Internationalization utilities";
      };
    };

    "Jinja2" = python.mkDerivation {
      name = "Jinja2-2.10.1";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/93/ea/d884a06f8c7f9b7afbc8138b762e80479fb17aedbbe2b06515a12de9378d/Jinja2-2.10.1.tar.gz";
        sha256 = "065c4f02ebe7f7cf559e49ee5a95fb800a9e4528727aec6f24402a5374c65013";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [
        self."Babel"
        self."MarkupSafe"
      ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://jinja.pocoo.org/";
        license = licenses.bsdOriginal;
        description = "A small but fast and easy to use stand-alone template engine written in pure python.";
      };
    };

    "MarkupSafe" = python.mkDerivation {
      name = "MarkupSafe-1.1.1";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/b9/2e/64db92e53b86efccfaea71321f597fa2e1b2bd3853d8ce658568f7a13094/MarkupSafe-1.1.1.tar.gz";
        sha256 = "29872e92839765e546828bb7754a68c418d927cd064fd4708fab9fe9c8bb116b";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://palletsprojects.com/p/markupsafe/";
        license = "BSD-3-Clause";
        description = "Safely add untrusted strings to HTML/XML markup.";
      };
    };

    "Pillow" = python.mkDerivation {
      name = "Pillow-6.0.0";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/81/1a/6b2971adc1bca55b9a53ed1efa372acff7e8b9913982a396f3fa046efaf8/Pillow-6.0.0.tar.gz";
        sha256 = "809c0a2ce9032cbcd7b5313f71af4bdc5c8c771cb86eb7559afd954cab82ebb5";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://python-pillow.org";
        license = "UNKNOWN";
        description = "Python Imaging Library (Fork)";
      };
    };

    "Pygments" = python.mkDerivation {
      name = "Pygments-2.4.2";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/7e/ae/26808275fc76bf2832deb10d3a3ed3107bc4de01b85dcccbe525f2cd6d1e/Pygments-2.4.2.tar.gz";
        sha256 = "881c4c157e45f30af185c1ffe8d549d48ac9127433f2c380c24b84572ad66297";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://pygments.org/";
        license = licenses.bsdOriginal;
        description = "Pygments is a syntax highlighting package written in Python.";
      };
    };

    "Sphinx" = python.mkDerivation {
      name = "Sphinx-2.1.1";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/97/49/2eb0837b5e8a7232c43e1ccf87caf49e2573ef370366511dfe9686cc97ce/Sphinx-2.1.1.tar.gz";
        sha256 = "15143166e786c7faa76fa990d3b6b38ebffe081ef81cffd1d656b07f3b28a1fa";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [
        self."Babel"
        self."Jinja2"
        self."Pygments"
        self."alabaster"
        self."docutils"
        self."imagesize"
        self."packaging"
        self."requests"
        self."snowballstemmer"
        self."sphinxcontrib-applehelp"
        self."sphinxcontrib-devhelp"
        self."sphinxcontrib-htmlhelp"
        self."sphinxcontrib-jsmath"
        self."sphinxcontrib-qthelp"
        self."sphinxcontrib-serializinghtml"
      ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://sphinx-doc.org/";
        license = licenses.bsdOriginal;
        description = "Python documentation generator";
      };
    };

    "actdiag" = python.mkDerivation {
      name = "actdiag-0.5.4";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/0e/9d/ccb245cbf5ef580755d3bd449dc6e0148f7570b6c0ca55a6bc183fd8e119/actdiag-0.5.4.tar.gz";
        sha256 = "983071777d9941093aaef3be1f67c198a8ac8d2bba264cdd1f337ca415ab46af";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [
        self."blockdiag"
        self."docutils"
      ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://blockdiag.com/";
        license = licenses.asl20;
        description = "actdiag generates activity-diagram image from text";
      };
    };

    "alabaster" = python.mkDerivation {
      name = "alabaster-0.7.12";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/cc/b4/ed8dcb0d67d5cfb7f83c4d5463a7614cb1d078ad7ae890c9143edebbf072/alabaster-0.7.12.tar.gz";
        sha256 = "a661d72d58e6ea8a57f7a86e37d86716863ee5e92788398526d58b26a4e4dc02";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://alabaster.readthedocs.io";
        license = "UNKNOWN";
        description = "A configurable sidebar-enabled Sphinx theme";
      };
    };

    "blockdiag" = python.mkDerivation {
      name = "blockdiag-1.5.4";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/0f/bd/2bfaef223e428742313d7fba6edca1e6d21cd2867dbd758874f403d82cbf/blockdiag-1.5.4.tar.gz";
        sha256 = "929125db1cb59145e09dc561021389c7ca71108ef4e4c51a12728eea5b75fccc";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [
        self."Pillow"
        self."docutils"
        self."funcparserlib"
        self."webcolors"
      ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://blockdiag.com/";
        license = licenses.asl20;
        description = "blockdiag generates block-diagram image from text";
      };
    };

    "certifi" = python.mkDerivation {
      name = "certifi-2019.3.9";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/06/b8/d1ea38513c22e8c906275d135818fee16ad8495985956a9b7e2bb21942a1/certifi-2019.3.9.tar.gz";
        sha256 = "b26104d6835d1f5e49452a26eb2ff87fe7090b89dfcaee5ea2212697e1e1d7ae";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://certifi.io/";
        license = licenses.mpl20;
        description = "Python package for providing Mozilla's CA Bundle.";
      };
    };

    "chardet" = python.mkDerivation {
      name = "chardet-3.0.4";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/fc/bb/a5768c230f9ddb03acc9ef3f0d4a3cf93462473795d18e9535498c8f929d/chardet-3.0.4.tar.gz";
        sha256 = "84ab92ed1c4d4f16916e05906b6b75a6c0fb5db821cc65e70cbd64a3e2a5eaae";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/chardet/chardet";
        license = licenses.lgpl3;
        description = "Universal encoding detector for Python 2 and 3";
      };
    };

    "docutils" = python.mkDerivation {
      name = "docutils-0.14";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/84/f4/5771e41fdf52aabebbadecc9381d11dea0fa34e4759b4071244fa094804c/docutils-0.14.tar.gz";
        sha256 = "51e64ef2ebfb29cae1faa133b3710143496eca21c530f3f71424d77687764274";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://docutils.sourceforge.net/";
        license = "public domain, Python, 2-Clause BSD, GPL 3 (see COPYING.txt)";
        description = "Docutils -- Python Documentation Utilities";
      };
    };

    "funcparserlib" = python.mkDerivation {
      name = "funcparserlib-0.3.6";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/cb/f7/b4a59c3ccf67c0082546eaeb454da1a6610e924d2e7a2a21f337ecae7b40/funcparserlib-0.3.6.tar.gz";
        sha256 = "b7992eac1a3eb97b3d91faa342bfda0729e990bd8a43774c1592c091e563c91d";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://code.google.com/p/funcparserlib/";
        license = licenses.mit;
        description = "Recursive descent parsing library based on functional combinators";
      };
    };

    "idna" = python.mkDerivation {
      name = "idna-2.8";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/ad/13/eb56951b6f7950cadb579ca166e448ba77f9d24efc03edd7e55fa57d04b7/idna-2.8.tar.gz";
        sha256 = "c357b3f628cf53ae2c4c05627ecc484553142ca23264e593d327bcde5e9c3407";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/kjd/idna";
        license = licenses.bsdOriginal;
        description = "Internationalized Domain Names in Applications (IDNA)";
      };
    };

    "imagesize" = python.mkDerivation {
      name = "imagesize-1.1.0";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/41/f5/3cf63735d54aa9974e544aa25858d8f9670ac5b4da51020bbfc6aaade741/imagesize-1.1.0.tar.gz";
        sha256 = "f3832918bc3c66617f92e35f5d70729187676313caa60c187eb0f28b8fe5e3b5";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/shibukawa/imagesize_py";
        license = licenses.mit;
        description = "Getting image size from png/jpeg/jpeg2000/gif file";
      };
    };

    "livereload" = python.mkDerivation {
      name = "livereload-2.6.1";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/27/26/85ba3851d2e4905be7d2d41082adca833182bb1d7de9dfc7f623383d36e1/livereload-2.6.1.tar.gz";
        sha256 = "89254f78d7529d7ea0a3417d224c34287ebfe266b05e67e51facaf82c27f0f66";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [
        self."six"
        self."tornado"
      ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/lepture/python-livereload";
        license = licenses.bsdOriginal;
        description = "Python LiveReload is an awesome tool for web developers";
      };
    };

    "nwdiag" = python.mkDerivation {
      name = "nwdiag-1.0.4";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/ca/5e/8b434f6655869c31b0b6d47f3972a469dfe14cb7f5b3b3b7c7413fa08f1c/nwdiag-1.0.4.tar.gz";
        sha256 = "002565875559789a2dfc5f578c07abdf44269c3f7cdf78d4809bdc4bdc2213fa";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [
        self."blockdiag"
        self."docutils"
      ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://blockdiag.com/";
        license = licenses.asl20;
        description = "nwdiag generates network-diagram image from text";
      };
    };

    "packaging" = python.mkDerivation {
      name = "packaging-19.0";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/16/51/d72654dbbaa4a4ffbf7cb0ecd7d12222979e0a660bf3f42acc47550bf098/packaging-19.0.tar.gz";
        sha256 = "0c98a5d0be38ed775798ece1b9727178c4469d9c3b4ada66e8e6b7849f8732af";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
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

    "pyparsing" = python.mkDerivation {
      name = "pyparsing-2.4.0";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/5d/3a/24d275393f493004aeb15a1beae2b4a3043526e8b692b65b4a9341450ebe/pyparsing-2.4.0.tar.gz";
        sha256 = "1873c03321fc118f4e9746baf201ff990ceb915f433f23b395f5580d1840cb2a";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/pyparsing/pyparsing/";
        license = licenses.mit;
        description = "Python parsing module";
      };
    };

    "pytz" = python.mkDerivation {
      name = "pytz-2019.1";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/df/d5/3e3ff673e8f3096921b3f1b79ce04b832e0100b4741573154b72b756a681/pytz-2019.1.tar.gz";
        sha256 = "d747dd3d23d77ef44c6a3526e274af6efeb0a6f1afd5a69ba4d5be4098c8e141";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://pythonhosted.org/pytz";
        license = licenses.mit;
        description = "World timezone definitions, modern and historical";
      };
    };

    "requests" = python.mkDerivation {
      name = "requests-2.22.0";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/01/62/ddcf76d1d19885e8579acb1b1df26a852b03472c0e46d2b959a714c90608/requests-2.22.0.tar.gz";
        sha256 = "11e007a8a2aa0323f5a921e9e6a2d7e4e67d9877e85773fba9ba6419025cbeb4";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
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

    "seqdiag" = python.mkDerivation {
      name = "seqdiag-0.9.6";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/b3/b5/aa0c9513df1898ecb4c3930d53e594b2298b3d5a535898f78c65cc0f45e1/seqdiag-0.9.6.tar.gz";
        sha256 = "78104e7644c1a4d3a5cacb68de6a7f720793f08dd78561ef0e9e80bed63702bf";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [
        self."blockdiag"
        self."docutils"
      ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://blockdiag.com/";
        license = licenses.asl20;
        description = "seqdiag generates sequence-diagram image from text";
      };
    };

    "six" = python.mkDerivation {
      name = "six-1.12.0";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/dd/bf/4138e7bfb757de47d1f4b6994648ec67a51efe58fa907c1e11e350cddfca/six-1.12.0.tar.gz";
        sha256 = "d16a0141ec1a18405cd4ce8b4613101da75da0e9a7aec5bdd4fa804d0e0eba73";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/benjaminp/six";
        license = licenses.mit;
        description = "Python 2 and 3 compatibility utilities";
      };
    };

    "snowballstemmer" = python.mkDerivation {
      name = "snowballstemmer-1.2.1";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/20/6b/d2a7cb176d4d664d94a6debf52cd8dbae1f7203c8e42426daa077051d59c/snowballstemmer-1.2.1.tar.gz";
        sha256 = "919f26a68b2c17a7634da993d91339e288964f93c274f1343e3bbbe2096e1128";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/shibukawa/snowball_py";
        license = licenses.bsdOriginal;
        description = "This package provides 16 stemmer algorithms (15 + Poerter English stemmer) generated from Snowball algorithms.";
      };
    };

    "sphinxcontrib-actdiag" = python.mkDerivation {
      name = "sphinxcontrib-actdiag-0.8.5";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/f4/44/b820b14ec3b010d90a3349ca968e5f6ed4dbc35c5c3875f5f5aad407d4a3/sphinxcontrib-actdiag-0.8.5.tar.gz";
        sha256 = "da3ba0fdfaaa0b855860ee94e97045249ddc0d4040d127247210d46acf068786";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [
        self."Sphinx"
        self."actdiag"
        self."blockdiag"
      ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/blockdiag/sphinxcontrib-actdiag";
        license = licenses.bsdOriginal;
        description = "Sphinx \"actdiag\" extension";
      };
    };

    "sphinxcontrib-applehelp" = python.mkDerivation {
      name = "sphinxcontrib-applehelp-1.0.1";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/1b/71/8bafa145e48131049dd4f731d6f6eeefe0c34c3017392adbec70171ad407/sphinxcontrib-applehelp-1.0.1.tar.gz";
        sha256 = "edaa0ab2b2bc74403149cb0209d6775c96de797dfd5b5e2a71981309efab3897";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "";
        license = "";
        description = "";
      };
    };

    "sphinxcontrib-blockdiag" = python.mkDerivation {
      name = "sphinxcontrib-blockdiag-1.5.5";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/04/50/7a43117a5a8a16acaceabc5ad69092fa1dacb11ef83c84fdf234e5a3502f/sphinxcontrib-blockdiag-1.5.5.tar.gz";
        sha256 = "7cdff966d8f372b9536374954314a6cf4280e0e48bc2321a4f25cc7f2114f8f0";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [
        self."Sphinx"
        self."blockdiag"
      ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/blockdiag/sphinxcontrib-blockdiag";
        license = licenses.bsdOriginal;
        description = "Sphinx \"blockdiag\" extension";
      };
    };

    "sphinxcontrib-devhelp" = python.mkDerivation {
      name = "sphinxcontrib-devhelp-1.0.1";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/57/5f/bf9a0f7454df68a7a29033a5cf8d53d0797ae2e426b1b419e4622726ec7d/sphinxcontrib-devhelp-1.0.1.tar.gz";
        sha256 = "6c64b077937330a9128a4da74586e8c2130262f014689b4b89e2d08ee7294a34";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "";
        license = "";
        description = "";
      };
    };

    "sphinxcontrib-htmlhelp" = python.mkDerivation {
      name = "sphinxcontrib-htmlhelp-1.0.2";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/f1/f2/88e9d6dc4a17f1e95871f8b634adefcc5d691334f7a121e9f384d1dc06fd/sphinxcontrib-htmlhelp-1.0.2.tar.gz";
        sha256 = "4670f99f8951bd78cd4ad2ab962f798f5618b17675c35c5ac3b2132a14ea8422";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "";
        license = "";
        description = "";
      };
    };

    "sphinxcontrib-jsmath" = python.mkDerivation {
      name = "sphinxcontrib-jsmath-1.0.1";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/b2/e8/9ed3830aeed71f17c026a07a5097edcf44b692850ef215b161b8ad875729/sphinxcontrib-jsmath-1.0.1.tar.gz";
        sha256 = "a9925e4a4587247ed2191a22df5f6970656cb8ca2bd6284309578f2153e0c4b8";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://sphinx-doc.org/";
        license = licenses.bsdOriginal;
        description = "A sphinx extension which renders display math in HTML via JavaScript";
      };
    };

    "sphinxcontrib-nwdiag" = python.mkDerivation {
      name = "sphinxcontrib-nwdiag-0.9.5";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/45/e0/97293d04f14f5e95932e1c842c726f9eaae336fd98a44c4f555f6c2783e7/sphinxcontrib-nwdiag-0.9.5.tar.gz";
        sha256 = "5b0ce78c1f7ccbbf33ca624574b117fa5334c8c17f98306a1e1b30e79db93491";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [
        self."Sphinx"
        self."blockdiag"
        self."nwdiag"
      ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/blockdiag/sphinxcontrib-nwdiag";
        license = licenses.bsdOriginal;
        description = "Sphinx \"nwdiag\" extension";
      };
    };

    "sphinxcontrib-qthelp" = python.mkDerivation {
      name = "sphinxcontrib-qthelp-1.0.2";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/0c/f0/690cd10603e3ea8d184b2fffde1d965dd337b87a1d5f7625d0f6791094f4/sphinxcontrib-qthelp-1.0.2.tar.gz";
        sha256 = "79465ce11ae5694ff165becda529a600c754f4bc459778778c7017374d4d406f";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "";
        license = "";
        description = "";
      };
    };

    "sphinxcontrib-seqdiag" = python.mkDerivation {
      name = "sphinxcontrib-seqdiag-0.8.5";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/10/59/5f746c6fe8a83ed7451b59e7787080adad8850a8a04d610713466fca3bca/sphinxcontrib-seqdiag-0.8.5.tar.gz";
        sha256 = "83c3fdac7e083c5b217f65359c03b75af753209028db6b261b196aff19e7003f";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [
        self."Sphinx"
        self."blockdiag"
        self."seqdiag"
      ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/blockdiag/sphinxcontrib-seqdiag";
        license = licenses.bsdOriginal;
        description = "Sphinx \"seqdiag\" extension";
      };
    };

    "sphinxcontrib-serializinghtml" = python.mkDerivation {
      name = "sphinxcontrib-serializinghtml-1.1.3";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/cd/cc/fd7d17cfae18e5a92564bb899bc05e13260d7a633f3cffdaad4e5f3ce46a/sphinxcontrib-serializinghtml-1.1.3.tar.gz";
        sha256 = "c0efb33f8052c04fd7a26c0a07f1678e8512e0faec19f4aa8f2473a8b81d5227";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "";
        license = "";
        description = "";
      };
    };

    "tornado" = python.mkDerivation {
      name = "tornado-6.0.2";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/03/3f/5f89d99fca3c0100c8cede4f53f660b126d39e0d6a1e943e95cc3ed386fb/tornado-6.0.2.tar.gz";
        sha256 = "457fcbee4df737d2defc181b9073758d73f54a6cfc1f280533ff48831b39f4a8";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://www.tornadoweb.org/";
        license = "http://www.apache.org/licenses/LICENSE-2.0";
        description = "Tornado is a Python web framework and asynchronous networking library, originally developed at FriendFeed.";
      };
    };

    "urllib3" = python.mkDerivation {
      name = "urllib3-1.25.3";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/4c/13/2386233f7ee40aa8444b47f7463338f3cbdf00c316627558784e3f542f07/urllib3-1.25.3.tar.gz";
        sha256 = "dbe59173209418ae49d485b87d1681aefa36252ee85884c31346debd19463232";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
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

    "webcolors" = python.mkDerivation {
      name = "webcolors-1.9.1";
      src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/70/8b/cf0ae06cf420718ef88080eca4ea971612831c99bfc43ebea826be6b52cb/webcolors-1.9.1.tar.gz";
        sha256 = "18c091bd4bd75efd1e9f84f5eca4a54f6e6485eaa3967d2a55700835a1b1c418";
      };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs ++ [ ];
      propagatedBuildInputs = [
        self."six"
      ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/ubernostrum/webcolors";
        license = "BSD 3-Clause";
        description = "A library for working with color names and color values formats defined by HTML and CSS.";
      };
    };
  };
  localOverridesFile = ./requirements_override.nix;
  localOverrides = import localOverridesFile { inherit pkgs python; };
  commonOverrides = [
        (import ../../nix/requirements_override.nix { inherit pkgs python ; })
  ];
  paramOverrides = [
    (overrides { inherit pkgs python; })
  ];
  allOverrides =
    (if (builtins.pathExists localOverridesFile)
     then [localOverrides] else [] ) ++ commonOverrides ++ paramOverrides;

in python.withPackages
   (fix' (pkgs.lib.fold
            extends
            generated
            allOverrides
         )
   )