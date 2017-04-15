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
        homepage = "";
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
        homepage = "";
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
        homepage = "";
        license = licenses.bsdOriginal;
        description = "Implements a XML/HTML/XHTML Markup safe string for Python";
      };
    };



    "Pillow" = python.mkDerivation {
      name = "Pillow-4.1.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/80/38/5cb561c68155834c596018c47caa44da88ed34b09579b921c0e493fb06c7/Pillow-4.1.0.tar.gz"; sha256 = "a0fd487fed4a35717401b7566e51a1520b34e7c0f7f2a315a6509f82bc86299f"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."olefile"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "";
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
        homepage = "";
        license = licenses.bsdOriginal;
        description = "Pygments is a syntax highlighting package written in Python.";
      };
    };



    "Sphinx" = python.mkDerivation {
      name = "Sphinx-1.5.5";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/64/78/9d63754981e97c8e7cf14500d262fc573145624d4c765d5047f58e3fdf4e/Sphinx-1.5.5.tar.gz"; sha256 = "4064ea6c56feeb268838cb8fbbee507d0c3d5d92fa63a7df935a916b52c9e2f5"; };
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
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "";
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
        homepage = "";
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
        homepage = "";
        license = licenses.bsdOriginal;
        description = "A configurable sidebar-enabled Sphinx theme";
      };
    };



    "appdirs" = python.mkDerivation {
      name = "appdirs-1.4.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/48/69/d87c60746b393309ca30761f8e2b49473d43450b150cb08f3c6df5c11be5/appdirs-1.4.3.tar.gz"; sha256 = "9e5896d1372858f8dd3344faf4e5014d21849c756c8d5701f78f8a103b372d92"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "";
        license = licenses.mit;
        description = "A small Python module for determining appropriate platform-specific dirs, e.g. a \"user data dir\".";
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
        homepage = "";
        license = licenses.asl20;
        description = "blockdiag generates block-diagram image from text";
      };
    };



    "docutils" = python.mkDerivation {
      name = "docutils-0.13.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/05/25/7b5484aca5d46915493f1fd4ecb63c38c333bd32aa9ad6e19da8d08895ae/docutils-0.13.1.tar.gz"; sha256 = "718c0f5fb677be0f34b781e04241c4067cbd9327b66bdd8e763201130f5175be"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "";
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
        homepage = "";
        license = licenses.mit;
        description = "Recursive descent parsing library based on functional combinators";
      };
    };



    "imagesize" = python.mkDerivation {
      name = "imagesize-0.7.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/53/72/6c6f1e787d9cab2cc733cf042f125abec07209a58308831c9f292504e826/imagesize-0.7.1.tar.gz"; sha256 = "0ab2c62b87987e3252f89d30b7cedbec12a01af9274af9ffa48108f2c13c6062"; };
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
      name = "livereload-2.5.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/e9/2e/c4972828cf526a2e5f5571d647fb2740df68f17e8084a9a1092f4d209f4c/livereload-2.5.1.tar.gz"; sha256 = "422de10d7ea9467a1ba27cbaffa84c74b809d96fb1598d9de4b9b676adf35e2c"; };
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
        homepage = "";
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
        homepage = "";
        license = licenses.bsdOriginal;
        description = "Python package to parse, read and write Microsoft OLE2 files (Structured Storage or Compound Document, Microsoft Office) - Improved version of the OleFileIO module from PIL, the Python Image Library.";
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
        homepage = "";
        license = licenses.bsdOriginal;
        description = "Core utilities for Python packages";
      };
    };



    "pyparsing" = python.mkDerivation {
      name = "pyparsing-2.2.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/3c/ec/a94f8cf7274ea60b5413df054f82a8980523efd712ec55a59e7c3357cf7c/pyparsing-2.2.0.tar.gz"; sha256 = "0832bcf47acd283788593e7a0f542407bd9550a55a8a8435214a1960e04bcb04"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "";
        license = licenses.mit;
        description = "Python parsing module";
      };
    };



    "pytz" = python.mkDerivation {
      name = "pytz-2017.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/a4/09/c47e57fc9c7062b4e83b075d418800d322caa87ec0ac21e6308bd3a2d519/pytz-2017.2.zip"; sha256 = "f5c056e8f62d45ba8215e5cb8f50dfccb198b4b9fbea8500674f3443e4689589"; };
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
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/16/09/37b69de7c924d318e51ece1c4ceb679bf93be9d05973bb30c35babd596e2/requests-2.13.0.tar.gz"; sha256 = "5722cd09762faa01276230270ff16af7acf7c5c45d623868d9ba116f15791ce8"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "";
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
        homepage = "";
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
        homepage = "";
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
        homepage = "";
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
        homepage = "";
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
        homepage = "";
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
        homepage = "";
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
        homepage = "";
        license = licenses.bsdOriginal;
        description = "Sphinx \"seqdiag\" extension";
      };
    };



    "tornado" = python.mkDerivation {
      name = "tornado-4.4.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/5c/0b/2e5cef0d30811532b27ece726fb66a41f63344af8b693c90cec9474d9022/tornado-4.4.3.tar.gz"; sha256 = "f267acc96d5cf3df0fd8a7bfb5a91c2eb4ec81d5962d1a7386ceb34c655634a8"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "";
        license = "License :: OSI Approved :: Apache Software License";
        description = "Tornado is a Python web framework and asynchronous networking library, originally developed at FriendFeed.";
      };
    };



    "webcolors" = python.mkDerivation {
      name = "webcolors-1.7";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/1c/11/d9fb5a7c872a941ad8b30a4be191253d5a9028834c4d69eab55bb6bc60be/webcolors-1.7.tar.gz"; sha256 = "e47e68644d41c0b1f1e4d939cfe4039bdf1ab31234df63c7a4f59d4766487206"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "";
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