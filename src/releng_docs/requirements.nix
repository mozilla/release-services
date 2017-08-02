# generated using pypi2nix tool (version: 1.8.0)
# See more at: https://github.com/garbas/pypi2nix
#
# COMMAND:
#   pypi2nix -v -V 3.5 -E pkgconfig zlib libjpeg openjpeg libtiff freetype lcms2 libwebp tcl -r requirements.txt
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

  commonBuildInputs = with pkgs; [ pkgconfig zlib libjpeg openjpeg libtiff freetype lcms2 libwebp tcl ];
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

    "Babel" = python.mkDerivation {
      name = "Babel-2.4.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/92/22/643f3b75f75e0220c5ef9f5b72b619ccffe9266170143a4821d4885198de/Babel-2.4.0.tar.gz"; sha256 = "8c98f5e5f8f5f088571f2c6bd88d530e331cbbcb95a7311a0db69d3dca7ec563"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
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
      name = "Jinja2-2.9.6";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/90/61/f820ff0076a2599dd39406dcb858ecb239438c02ce706c8e91131ab9c7f1/Jinja2-2.9.6.tar.gz"; sha256 = "ddaa01a212cd6d641401cb01b605f4a4d9f37bfc93043d7f760ec70fb99ff9ff"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
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
      name = "MarkupSafe-1.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/4d/de/32d741db316d8fdb7680822dd37001ef7a448255de9699ab4bfcbdf4172b/MarkupSafe-1.0.tar.gz"; sha256 = "a6be69091dac236ea9c6bc7d012beab42010fa914c459791d627dad4910eb665"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/pallets/markupsafe";
        license = licenses.bsdOriginal;
        description = "Implements a XML/HTML/XHTML Markup safe string for Python";
      };
    };



    "Pillow" = python.mkDerivation {
      name = "Pillow-4.2.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/55/aa/f7f983fb72710a9daa4b3374b7c160091d3f94f5c09221f9336ade9027f3/Pillow-4.2.1.tar.gz"; sha256 = "c724f65870e545316f9e82e4c6d608ab5aa9dd82d5185e5b2e72119378740073"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."olefile"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://python-pillow.org";
        license = "Standard PIL License";
        description = "Python Imaging Library (Fork)";
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



    "Sphinx" = python.mkDerivation {
      name = "Sphinx-1.6.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/10/91/ceb2e0d763e0c626f7afd7e3272a5bb76dd06eed1f0b908270ea31984062/Sphinx-1.6.3.tar.gz"; sha256 = "af8bdb8c714552b77d01d4536e3d6d2879d6cb9d25423d29163d5788e27046e6"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Babel"
      self."Jinja2"
      self."Pygments"
      self."alabaster"
      self."docutils"
      self."imagesize"
      self."requests"
      self."six"
      self."snowballstemmer"
      self."sphinxcontrib-websupport"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://sphinx-doc.org/";
        license = licenses.bsdOriginal;
        description = "Python documentation generator";
      };
    };



    "actdiag" = python.mkDerivation {
      name = "actdiag-0.5.4";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/0e/9d/ccb245cbf5ef580755d3bd449dc6e0148f7570b6c0ca55a6bc183fd8e119/actdiag-0.5.4.tar.gz"; sha256 = "983071777d9941093aaef3be1f67c198a8ac8d2bba264cdd1f337ca415ab46af"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
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
      name = "alabaster-0.7.10";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/d0/a5/e3a9ad3ee86aceeff71908ae562580643b955ea1b1d4f08ed6f7e8396bd7/alabaster-0.7.10.tar.gz"; sha256 = "37cdcb9e9954ed60912ebc1ca12a9d12178c26637abdf124e3cde2341c257fe0"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://alabaster.readthedocs.io";
        license = licenses.bsdOriginal;
        description = "A configurable sidebar-enabled Sphinx theme";
      };
    };



    "blockdiag" = python.mkDerivation {
      name = "blockdiag-1.5.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/5f/fc/a977375277e22f9a90e04fe7bd61e49c556bb1c1d7c8065277c21ba2fef9/blockdiag-1.5.3.tar.gz"; sha256 = "5ea3501fca0ca40fbacccc6f4ca177750e4b610009e021faa4868c0f6480ae8b"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
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
      name = "certifi-2017.7.27.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/20/d0/3f7a84b0c5b89e94abbd073a5f00c7176089f526edb056686751d5064cbd/certifi-2017.7.27.1.tar.gz"; sha256 = "40523d2efb60523e113b44602298f0960e900388cf3bb6043f645cf57ea9e3f5"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://certifi.io/";
        license = "MPL-2.0";
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



    "funcparserlib" = python.mkDerivation {
      name = "funcparserlib-0.3.6";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/cb/f7/b4a59c3ccf67c0082546eaeb454da1a6610e924d2e7a2a21f337ecae7b40/funcparserlib-0.3.6.tar.gz"; sha256 = "b7992eac1a3eb97b3d91faa342bfda0729e990bd8a43774c1592c091e563c91d"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://code.google.com/p/funcparserlib/";
        license = licenses.mit;
        description = "Recursive descent parsing library based on functional combinators";
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



    "imagesize" = python.mkDerivation {
      name = "imagesize-0.7.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/53/72/6c6f1e787d9cab2cc733cf042f125abec07209a58308831c9f292504e826/imagesize-0.7.1.tar.gz"; sha256 = "0ab2c62b87987e3252f89d30b7cedbec12a01af9274af9ffa48108f2c13c6062"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/shibukawa/imagesize_py";
        license = licenses.mit;
        description = "Getting image size from png/jpeg/jpeg2000/gif file";
      };
    };



    "livereload" = python.mkDerivation {
      name = "livereload-2.5.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/e9/2e/c4972828cf526a2e5f5571d647fb2740df68f17e8084a9a1092f4d209f4c/livereload-2.5.1.tar.gz"; sha256 = "422de10d7ea9467a1ba27cbaffa84c74b809d96fb1598d9de4b9b676adf35e2c"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
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
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/ca/5e/8b434f6655869c31b0b6d47f3972a469dfe14cb7f5b3b3b7c7413fa08f1c/nwdiag-1.0.4.tar.gz"; sha256 = "002565875559789a2dfc5f578c07abdf44269c3f7cdf78d4809bdc4bdc2213fa"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
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



    "olefile" = python.mkDerivation {
      name = "olefile-0.44";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/35/17/c15d41d5a8f8b98cc3df25eb00c5cee76193114c78e5674df6ef4ac92647/olefile-0.44.zip"; sha256 = "61f2ca0cd0aa77279eb943c07f607438edf374096b66332fae1ee64a6f0f73ad"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://www.decalage.info/python/olefileio";
        license = licenses.bsdOriginal;
        description = "Python package to parse, read and write Microsoft OLE2 files (Structured Storage or Compound Document, Microsoft Office) - Improved version of the OleFileIO module from PIL, the Python Image Library.";
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
      name = "requests-2.18.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/07/2e/81fdfdfac91cf3cb2518fb149ac67caf0e081b485eab68e9aee63396f7e8/requests-2.18.2.tar.gz"; sha256 = "5b26fcc5e72757a867e4d562333f841eddcef93548908a1bb1a9207260618da9"; };
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



    "seqdiag" = python.mkDerivation {
      name = "seqdiag-0.9.5";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/0c/4d/b15369e167196501d2177bfa22df00acceedece3c2709ccc3089da38cb49/seqdiag-0.9.5.tar.gz"; sha256 = "994402cb19fef77ee113d18810aa397a7290553cda5f900be2bb44e2c7742657"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
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



    "snowballstemmer" = python.mkDerivation {
      name = "snowballstemmer-1.2.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/20/6b/d2a7cb176d4d664d94a6debf52cd8dbae1f7203c8e42426daa077051d59c/snowballstemmer-1.2.1.tar.gz"; sha256 = "919f26a68b2c17a7634da993d91339e288964f93c274f1343e3bbbe2096e1128"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/shibukawa/snowball_py";
        license = licenses.bsdOriginal;
        description = "This package provides 16 stemmer algorithms (15 + Poerter English stemmer) generated from Snowball algorithms.";
      };
    };



    "sphinxcontrib-actdiag" = python.mkDerivation {
      name = "sphinxcontrib-actdiag-0.8.5";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/f4/44/b820b14ec3b010d90a3349ca968e5f6ed4dbc35c5c3875f5f5aad407d4a3/sphinxcontrib-actdiag-0.8.5.tar.gz"; sha256 = "da3ba0fdfaaa0b855860ee94e97045249ddc0d4040d127247210d46acf068786"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
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



    "sphinxcontrib-blockdiag" = python.mkDerivation {
      name = "sphinxcontrib-blockdiag-1.5.5";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/04/50/7a43117a5a8a16acaceabc5ad69092fa1dacb11ef83c84fdf234e5a3502f/sphinxcontrib-blockdiag-1.5.5.tar.gz"; sha256 = "7cdff966d8f372b9536374954314a6cf4280e0e48bc2321a4f25cc7f2114f8f0"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
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



    "sphinxcontrib-nwdiag" = python.mkDerivation {
      name = "sphinxcontrib-nwdiag-0.9.5";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/45/e0/97293d04f14f5e95932e1c842c726f9eaae336fd98a44c4f555f6c2783e7/sphinxcontrib-nwdiag-0.9.5.tar.gz"; sha256 = "5b0ce78c1f7ccbbf33ca624574b117fa5334c8c17f98306a1e1b30e79db93491"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
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



    "sphinxcontrib-seqdiag" = python.mkDerivation {
      name = "sphinxcontrib-seqdiag-0.8.5";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/10/59/5f746c6fe8a83ed7451b59e7787080adad8850a8a04d610713466fca3bca/sphinxcontrib-seqdiag-0.8.5.tar.gz"; sha256 = "83c3fdac7e083c5b217f65359c03b75af753209028db6b261b196aff19e7003f"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
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



    "sphinxcontrib-websupport" = python.mkDerivation {
      name = "sphinxcontrib-websupport-1.0.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/c5/6b/f0630436b931ad4f8331a9399ca18a7d447f0fcc0c7178fb56b1aee68d01/sphinxcontrib-websupport-1.0.1.tar.gz"; sha256 = "7a85961326aa3a400cd4ad3c816d70ed6f7c740acd7ce5d78cd0a67825072eb9"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://sphinx-doc.org/";
        license = licenses.bsdOriginal;
        description = "Sphinx API for Web Apps";
      };
    };



    "tornado" = python.mkDerivation {
      name = "tornado-4.5.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/df/42/a180ee540e12e2ec1007ac82a42b09dd92e5461e09c98bf465e98646d187/tornado-4.5.1.tar.gz"; sha256 = "db0904a28253cfe53e7dedc765c71596f3c53bb8a866ae50123320ec1a7b73fd"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://www.tornadoweb.org/";
        license = "License :: OSI Approved :: Apache Software License";
        description = "Tornado is a Python web framework and asynchronous networking library, originally developed at FriendFeed.";
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



    "webcolors" = python.mkDerivation {
      name = "webcolors-1.7";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/1c/11/d9fb5a7c872a941ad8b30a4be191253d5a9028834c4d69eab55bb6bc60be/webcolors-1.7.tar.gz"; sha256 = "e47e68644d41c0b1f1e4d939cfe4039bdf1ab31234df63c7a4f59d4766487206"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/ubernostrum/webcolors";
        license = licenses.bsdOriginal;
        description = "A library for working with color names and color value formats defined by the HTML and CSS specifications for use in documents on the Web.";
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