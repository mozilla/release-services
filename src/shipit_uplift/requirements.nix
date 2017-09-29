# generated using pypi2nix tool (version: 1.8.0)
# See more at: https://github.com/garbas/pypi2nix
#
# COMMAND:
#   pypi2nix -v -V 3.5 -E postgresql -r requirements.txt -r requirements-dev.txt
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

  commonBuildInputs = with pkgs; [ postgresql ];
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

    "Flask" = python.mkDerivation {
      name = "Flask-0.12.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/eb/12/1c7bd06fcbd08ba544f25bf2c6612e305a70ea51ca0eda8007344ec3f123/Flask-0.12.2.tar.gz"; sha256 = "49f44461237b69ecd901cc7ce66feea0319b9158743dd27a2899962ab214dac1"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Jinja2"
      self."Werkzeug"
      self."click"
      self."itsdangerous"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/pallets/flask/";
        license = licenses.bsdOriginal;
        description = "A microframework based on Werkzeug, Jinja2 and good intentions";
      };
    };



    "Flask-Cache" = python.mkDerivation {
      name = "Flask-Cache-0.13.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/91/c4/f71095437bd4b691c63f240e72a20c57e2c216085cbc271f79665885d3da/Flask-Cache-0.13.1.tar.gz"; sha256 = "90126ca9bc063854ef8ee276e95d38b2b4ec8e45fd77d5751d37971ee27c7ef4"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Flask"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/thadeusb/flask-cache";
        license = licenses.bsdOriginal;
        description = "Adds cache support to your Flask application";
      };
    };



    "Flask-Cors" = python.mkDerivation {
      name = "Flask-Cors-3.0.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/64/e8/e6bcf79dcad7b7c10f8c8c35d78b5710f2ddcd8ed38e607dd6a4853ab8a8/Flask-Cors-3.0.3.tar.gz"; sha256 = "62ebc5ad80dc21ca0ea9f57466c2c74e24a62274af890b391790c260eb7b754b"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Flask"
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/corydolphin/flask-cors";
        license = licenses.mit;
        description = "A Flask extension adding a decorator for CORS support";
      };
    };



    "Flask-Login" = python.mkDerivation {
      name = "Flask-Login-0.4.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/70/96/20cae731ef27084dcb183f3a6e3073d0232f10c1fd7be76729bd7bd4b994/Flask-Login-0.4.0.tar.gz"; sha256 = "d25e356b14a59f52da0ab30c31c2ad285fa23a840f0f6971df7ed247c77082a7"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Flask"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/maxcountryman/flask-login";
        license = licenses.mit;
        description = "User session management for Flask";
      };
    };



    "Flask-Migrate" = python.mkDerivation {
      name = "Flask-Migrate-2.1.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/2f/84/9a7d3dafd45b41931f2833a28f96537cca1771583102204310a6246f750e/Flask-Migrate-2.1.1.tar.gz"; sha256 = "b709ca8642559c3c5a81a33ab10839fa052177accd5ba821047a99db635255ed"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Flask"
      self."Flask-SQLAlchemy"
      self."alembic"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/miguelgrinberg/flask-migrate/";
        license = licenses.mit;
        description = "SQLAlchemy database migrations for Flask applications using Alembic";
      };
    };



    "Flask-SQLAlchemy" = python.mkDerivation {
      name = "Flask-SQLAlchemy-2.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/15/f0/0c90391352db8244321e22604d93cb6a4e3c538e9ab512b35ee5359b8d74/Flask-SQLAlchemy-2.2.tar.gz"; sha256 = "f0d8241efba723d7b878f73550f5d3c0fbb042416123b52b36640b7491fa208b"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Flask"
      self."SQLAlchemy"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/mitsuhiko/flask-sqlalchemy";
        license = licenses.bsdOriginal;
        description = "Adds SQLAlchemy support to your Flask application";
      };
    };



    "Jinja2" = python.mkDerivation {
      name = "Jinja2-2.9.6";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/90/61/f820ff0076a2599dd39406dcb858ecb239438c02ce706c8e91131ab9c7f1/Jinja2-2.9.6.tar.gz"; sha256 = "ddaa01a212cd6d641401cb01b605f4a4d9f37bfc93043d7f760ec70fb99ff9ff"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."MarkupSafe"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://jinja.pocoo.org/";
        license = licenses.bsdOriginal;
        description = "A small but fast and easy to use stand-alone template engine written in pure python.";
      };
    };



    "Logbook" = python.mkDerivation {
      name = "Logbook-1.1.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/a2/d1/b5d12094f5a5b8f456198991c44b56faf72411e58dc166e71593ff2febea/Logbook-1.1.0.tar.gz"; sha256 = "0e37a18f4f8244b02a1c44cfd2a3bab9513e6e22b67986ab6a91d52b87f0940b"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Jinja2"
      self."SQLAlchemy"
      self."pytest"
      self."redis"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://logbook.pocoo.org/";
        license = licenses.bsdOriginal;
        description = "A logging replacement for Python";
      };
    };



    "Mako" = python.mkDerivation {
      name = "Mako-1.0.7";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/eb/f3/67579bb486517c0d49547f9697e36582cd19dafb5df9e687ed8e22de57fa/Mako-1.0.7.tar.gz"; sha256 = "4e02fde57bd4abb5ec400181e4c314f56ac3e49ba4fb8b0d50bba18cb27d25ae"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."MarkupSafe"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://www.makotemplates.org/";
        license = licenses.mit;
        description = "A super-fast templating language that borrows the  best ideas from the existing templating languages.";
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



    "SQLAlchemy" = python.mkDerivation {
      name = "SQLAlchemy-1.1.14";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/a3/d1/eacdedd964ad43fbc4cc7110dac33fbf1dbd7bf50dedb4dc1799c42972c1/SQLAlchemy-1.1.14.tar.gz"; sha256 = "f1191e29e35b6fe1aef7175a09b1707ebb7bd08d0b17cb0feada76c49e5a2d1e"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."psycopg2"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://www.sqlalchemy.org";
        license = licenses.mit;
        description = "Database Abstraction Library";
      };
    };



    "Werkzeug" = python.mkDerivation {
      name = "Werkzeug-0.12.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/56/41/c095a77eb2dd69bf278dd664a97d3416af04e9ba1a00b8c138f772741d31/Werkzeug-0.12.2.tar.gz"; sha256 = "903a7b87b74635244548b30d30db4c8947fe64c5198f58899ddcd3a13c23bb26"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://werkzeug.pocoo.org/";
        license = licenses.bsdOriginal;
        description = "The Swiss Army knife of Python web development";
      };
    };



    "aiohttp" = python.mkDerivation {
      name = "aiohttp-2.2.5";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/1e/d4/c1206b016b42a0b223aadb559318966b64ec27e5406bed79c36356e62082/aiohttp-2.2.5.tar.gz"; sha256 = "af5bfdd164256118a0a306b3f7046e63207d1f8cba73a67dcc0bd858dcfcd3bc"; };
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



    "alembic" = python.mkDerivation {
      name = "alembic-0.9.5";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/52/ec/4514b7b9a849e9b35ebf60888c9a1cf8262e927e9a9c8f894ffbf5a76ec7/alembic-0.9.5.tar.gz"; sha256 = "8bdcb4babaa16b9a826f8084949cc2665cb328ecf7b89b3224b0ab85bd16fd05"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Mako"
      self."SQLAlchemy"
      self."python-dateutil"
      self."python-editor"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://bitbucket.org/zzzeek/alembic";
        license = licenses.mit;
        description = "A database migration tool for SQLAlchemy.";
      };
    };



    "amqp" = python.mkDerivation {
      name = "amqp-2.2.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/e0/70/9ab9ccd8247fb7d2adb717e9f6a0ed358c9e1ab2c349048b0352f9e80ee2/amqp-2.2.2.tar.gz"; sha256 = "cba1ace9d4ff6049b190d8b7991f9c1006b443a5238021aca96dd6ad2ac9da22"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."vine"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/celery/py-amqp";
        license = licenses.bsdOriginal;
        description = "Low-level AMQP client for Python (fork of amqplib).";
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



    "blinker" = python.mkDerivation {
      name = "blinker-1.4";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/1b/51/e2a9f3b757eb802f61dc1f2b09c8c99f6eb01cf06416c0671253536517b6/blinker-1.4.tar.gz"; sha256 = "471aee25f3992bd325afa3772f1063dbdbbca947a041b8b89466dc00d606f8b6"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://pythonhosted.org/blinker/";
        license = licenses.mit;
        description = "Fast, simple object-to-object and broadcast signaling";
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



    "clickclick" = python.mkDerivation {
      name = "clickclick-1.2.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/b8/cf/2d1fb0c967616e7cd3a8e6a3aca38bc50b50137d9bc7f46cdb3e6fe03361/clickclick-1.2.2.tar.gz"; sha256 = "4a890aaa9c3990cfabd446294eb34e3dc89701101ac7b41c1bff85fc210f6d23"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."PyYAML"
      self."click"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/zalando/python-clickclick";
        license = licenses.asl20;
        description = "Click utility functions";
      };
    };



    "connexion" = python.mkDerivation {
      name = "connexion-1.1.15";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/6b/bd/c89a35b80744ccc0c77836fe0418a7f8ed2f85a1930e23157088c1560cec/connexion-1.1.15.tar.gz"; sha256 = "5dd022488438f4b75d8fa0435cd95b402f1bce1a6bb3599a0d568ba2c3e70afe"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Flask"
      self."PyYAML"
      self."clickclick"
      self."inflection"
      self."jsonschema"
      self."pytest"
      self."requests"
      self."six"
      self."swagger-spec-validator"
      self."typing"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/zalando/connexion";
        license = licenses.asl20;
        description = "Connexion - API first applications with OpenAPI/Swagger and Flask";
      };
    };



    "cookies" = python.mkDerivation {
      name = "cookies-2.2.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/f3/95/b66a0ca09c5ec9509d8729e0510e4b078d2451c5e33f47bd6fc33c01517c/cookies-2.2.1.tar.gz"; sha256 = "d6b698788cae4cfa4e62ef8643a9ca332b79bd96cb314294b864ae8d7eb3ee8e"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/sashahart/cookies";
        license = licenses.mit;
        description = "Friendlier RFC 6265-compliant cookie parser/renderer";
      };
    };



    "fancycompleter" = python.mkDerivation {
      name = "fancycompleter-0.7";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/93/33/0fc5fd5ffcd05e60af4f923d0d722e280a3ea348c00f25d0081c794e075c/fancycompleter-0.7.tar.gz"; sha256 = "5044bf91766dde3addfea81aaf36bacce89e1a872a10567f57e51f981c531eb7"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://bitbucket.org/antocuni/fancycompleter";
        license = licenses.bsdOriginal;
        description = "colorful TAB completion for Python prompt";
      };
    };



    "flake8" = python.mkDerivation {
      name = "flake8-3.4.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/c8/82/13c6502074a8da93938de43b7386b60073afa528b07004643890ba02de9a/flake8-3.4.1.tar.gz"; sha256 = "c20044779ff848f67f89c56a0e4624c04298cd476e25253ac0c36f910a1a11d8"; };
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



    "flask-oidc" = python.mkDerivation {
      name = "flask-oidc-1.1.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/be/cc/7bbead3a11dd7623f7499e4e3186509efeced28ec935ba8d995b3788c586/flask-oidc-1.1.1.tar.gz"; sha256 = "c2b73664dbcd3f10b78c0df4eb02fa26ec5752a60c1e134f8f8b9ce02a90c5ab"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Flask"
      self."itsdangerous"
      self."oauth2client"
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/puiterwijk/flask-oidc";
        license = licenses.bsdOriginal;
        description = "OpenID Connect extension for Flask";
      };
    };



    "flask-talisman" = python.mkDerivation {
      name = "flask-talisman-0.4.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/ad/9f/1bf427261d566d879aad9d845cdb66dd90fb6fa3f9fdbf3fa8b5e79606cf/flask-talisman-0.4.0.tar.gz"; sha256 = "3ba3f7292bb75d152ea817a02600478c27ae5bdda24229b2248c0ac1d614ba72"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/GoogleCloudPlatform/flask-talisman";
        license = "License :: OSI Approved :: Apache Software License";
        description = "HTTP security headers for Flask.";
      };
    };



    "gunicorn" = python.mkDerivation {
      name = "gunicorn-19.7.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/30/3a/10bb213cede0cc4d13ac2263316c872a64bf4c819000c8ccd801f1d5f822/gunicorn-19.7.1.tar.gz"; sha256 = "eee1169f0ca667be05db3351a0960765620dad53f53434262ff8901b68a1b622"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://gunicorn.org";
        license = licenses.mit;
        description = "WSGI HTTP Server for UNIX";
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



    "inflection" = python.mkDerivation {
      name = "inflection-0.3.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/d5/35/a6eb45b4e2356fe688b21570864d4aa0d0a880ce387defe9c589112077f8/inflection-0.3.1.tar.gz"; sha256 = "18ea7fb7a7d152853386523def08736aa8c32636b047ade55f7578c4edeb16ca"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/jpvanhal/inflection";
        license = licenses.mit;
        description = "A port of Ruby on Rails inflector to Python";
      };
    };



    "inotify" = python.mkDerivation {
      name = "inotify-0.2.8";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/ab/3b/ad48cb45af4af32341fc6bf28497081a885d1e23777d2827f3c61d734f02/inotify-0.2.8.tar.gz"; sha256 = "837638060997c2c1a87c015f56479f0e05d8403a47c6fe729aacd3746b885fe9"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/dsoprea/PyInotify";
        license = "GPL 2";
        description = "An adapter to Linux kernel support for inotify directory-watching.";
      };
    };



    "itsdangerous" = python.mkDerivation {
      name = "itsdangerous-0.24";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/dc/b4/a60bcdba945c00f6d608d8975131ab3f25b22f2bcfe1dab221165194b2d4/itsdangerous-0.24.tar.gz"; sha256 = "cbb3fcf8d3e33df861709ecaf89d9e6629cff0a217bc2848f1b41cd30d360519"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/mitsuhiko/itsdangerous";
        license = licenses.bsdOriginal;
        description = "Various helpers to pass trusted data to untrusted environments and back.";
      };
    };



    "jsonschema" = python.mkDerivation {
      name = "jsonschema-2.6.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/58/b9/171dbb07e18c6346090a37f03c7e74410a1a56123f847efed59af260a298/jsonschema-2.6.0.tar.gz"; sha256 = "6ff5f3180870836cae40f06fa10419f557208175f13ad7bc26caa77beb1f6e02"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/Julian/jsonschema";
        license = licenses.mit;
        description = "An implementation of JSON Schema validation for Python";
      };
    };



    "kombu" = python.mkDerivation {
      name = "kombu-4.1.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/03/5e/1a47d1e543d4943d65330af4e4406049f443878818fb65bfdc651bb93a96/kombu-4.1.0.tar.gz"; sha256 = "4249d9dd9dbf1fcec471d1c2def20653c9310dd1a217272d77e4844f9d5273cb"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."PyYAML"
      self."SQLAlchemy"
      self."amqp"
      self."redis"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://kombu.readthedocs.io";
        license = licenses.bsdOriginal;
        description = "Messaging library for Python.";
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



    "mozilla-backend-common" = python.mkDerivation {
      name = "mozilla-backend-common-1.0.0";
      src = ./../../lib/backend_common;
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Flask"
      self."Flask-Cache"
      self."Flask-Cors"
      self."Flask-Login"
      self."Flask-Migrate"
      self."Flask-SQLAlchemy"
      self."Jinja2"
      self."Logbook"
      self."blinker"
      self."connexion"
      self."flake8"
      self."flake8-coding"
      self."flake8-quotes"
      self."flask-oidc"
      self."flask-talisman"
      self."inotify"
      self."kombu"
      self."mozilla-cli-common"
      self."pdbpp"
      self."pytest"
      self."responses"
      self."taskcluster"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/garbas/mozilla-releng";
        license = "MPL2";
        description = "Services behind https://mozilla-releng.net";
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
      name = "multidict-3.2.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/68/a6/d241f9d1ed5ca55a819329c2f98c6833a2d8f25463bc03c44039cd13639c/multidict-3.2.0.tar.gz"; sha256 = "e27a7a95317371c15ecda7206f6e8c144f10a337bb2c3e61b5176deafbb88cb2"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/aio-libs/multidict/";
        license = licenses.asl20;
        description = "multidict implementation";
      };
    };



    "oauth2client" = python.mkDerivation {
      name = "oauth2client-4.1.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/50/30/f89a4fc014a03e180840d432e73ffb96da422f2a8094ff3539f0f0c46661/oauth2client-4.1.2.tar.gz"; sha256 = "bd3062c06f8b10c6ef7a890b22c2740e5f87d61b6e1f4b1c90d069cdfc9dadb5"; };
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



    "pdbpp" = python.mkDerivation {
      name = "pdbpp-0.9.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/46/0f/cee9549c6fe6a66cd8a411b6858e5eaa57177671d097acd39b14ca1cc152/pdbpp-0.9.1.tar.gz"; sha256 = "4a8099079150bbd6b6eedcd6cc42573871bec7d7e7e094feeaca01a62f65959c"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Pygments"
      self."fancycompleter"
      self."wmctrl"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/antocuni/pdb";
        license = licenses.bsdOriginal;
        description = "pdb++, a drop-in replacement for pdb";
      };
    };



    "psycopg2" = python.mkDerivation {
      name = "psycopg2-2.7.3.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/6b/fb/15c687eda2f925f0ff59373063fdb408471b4284714a7761daaa65c01f15/psycopg2-2.7.3.1.tar.gz"; sha256 = "9b7b16e26448b43cf167f785d8b5345007731ebf153a510e12dae826800caa65"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://initd.org/psycopg/";
        license = licenses.lgpl2;
        description = "psycopg2 - Python-PostgreSQL Database Adapter";
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



    "pyasn1" = python.mkDerivation {
      name = "pyasn1-0.3.5";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/bc/85/029f5f4d4fa8a487538ce597932cf3601bba3392c85d74eae148fe6ac5d3/pyasn1-0.3.5.tar.gz"; sha256 = "c7a1186416bcdaf19b56f5b2506200306d7d4cf222d3d7c2d4cb600ccacdaf1b"; };
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
      name = "pyasn1-modules-0.1.4";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/66/6b/f5582cbf3b920896ce1b97bde3894599b3dec31301ef79ae7ea0022f5577/pyasn1-modules-0.1.4.tar.gz"; sha256 = "b07c17bdb34d6f64aafea6269f2e8fb306a57473f0f38d9a6ca389d6ab30ac4a"; };
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



    "pytest" = python.mkDerivation {
      name = "pytest-3.2.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/63/4a/db317d848325ba77e4ed498860b40ab53a8b49f1ae13612bc8aee75634f0/pytest-3.2.2.tar.gz"; sha256 = "f46e49e0340a532764991c498244a60e3a37d7424a532b3ff1a6a7653f1a403a"; };
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



    "python-editor" = python.mkDerivation {
      name = "python-editor-1.0.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/65/1e/adf6e000ea5dc909aa420352d6ba37f16434c8a3c2fa030445411a1ed545/python-editor-1.0.3.tar.gz"; sha256 = "a3c066acee22a1c94f63938341d4fb374e3fdd69366ed6603d7b24bed1efc565"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/fmoo/python-editor";
        license = "License :: OSI Approved :: Apache Software License";
        description = "Programmatically open an editor, capture the result.";
      };
    };



    "raven" = python.mkDerivation {
      name = "raven-6.1.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/ee/82/9a85650c174920f5bd260b8138a1db7190156e55193b0a1d03d2fa7a2811/raven-6.1.0.tar.gz"; sha256 = "02cabffb173b99d860a95d4908e8b1864aad1b8452146e13fd7e212aa576a884"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."Flask"
      self."Flask-Login"
      self."Logbook"
      self."blinker"
      self."flake8"
      self."pycodestyle"
      self."pytest"
      self."requests"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/getsentry/raven-python";
        license = licenses.bsdOriginal;
        description = "Raven is a client for Sentry (https://getsentry.com)";
      };
    };



    "redis" = python.mkDerivation {
      name = "redis-2.10.6";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/09/8d/6d34b75326bf96d4139a2ddd8e74b80840f800a0a79f9294399e212cb9a7/redis-2.10.6.tar.gz"; sha256 = "a22ca993cea2962dbb588f9f30d0015ac4afcc45bee27d3978c0dbe9e97c6c0f"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/andymccurdy/redis-py";
        license = licenses.mit;
        description = "Python client for Redis key-value store";
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



    "responses" = python.mkDerivation {
      name = "responses-0.7.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/40/3a/bccc47f14d2ac1daeab1f574fbe985b9858ce343188fdbbfe2cea8c1ce4e/responses-0.7.0.tar.gz"; sha256 = "912da86d9d9ca6e02f00e5ecd61d08992ab1511858260bd5df8b2b1e51a6dc9f"; };
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
        homepage = "https://github.com/getsentry/responses";
        license = licenses.asl20;
        description = "A utility library for mocking out the `requests` Python library.";
      };
    };



    "rq" = python.mkDerivation {
      name = "rq-0.8.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/2b/6b/4b0b41b356bad12f2927d412508f8ca17dc85a113bb951b1f1b39f089989/rq-0.8.2.tar.gz"; sha256 = "1d93356c1c3073b543506cc3662f50744af8e28848eb65dffb06e0c2628b89f6"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."click"
      self."redis"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://github.com/nvie/rq/";
        license = licenses.bsdOriginal;
        description = "RQ is a simple, lightweight, library for creating background jobs, and processing them.";
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



    "six" = python.mkDerivation {
      name = "six-1.11.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/16/d8/bc6316cf98419719bd59c91742194c111b6f2e85abac88e496adefaf7afe/six-1.11.0.tar.gz"; sha256 = "70e8a77beed4562e7f14fe23a786b54f6296e34344c23bc42f07b15018ff98e9"; };
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



    "swagger-spec-validator" = python.mkDerivation {
      name = "swagger-spec-validator-2.1.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/e3/2f/3767da696617ee72190361805dff4bca68a611d4673de848857654789534/swagger-spec-validator-2.1.0.tar.gz"; sha256 = "dc9219c6572ce0def6e1c160ca253c0e7fcde75812628f0c0199334f85bd138e"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [
      self."jsonschema"
      self."six"
    ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/Yelp/swagger_spec_validator";
        license = licenses.asl20;
        description = "Validation of Swagger specifications";
      };
    };



    "taskcluster" = python.mkDerivation {
      name = "taskcluster-1.3.5";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/09/f3/b5a7b58271664a54bfb33c6e9dde0e7b8dcd15f272cc3e3e81a63cd92b7b/taskcluster-1.3.5.tar.gz"; sha256 = "67373888f4d3c7adf8d0198db0535ff414a71239868532a5522d0285a20d0cf1"; };
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



    "typing" = python.mkDerivation {
      name = "typing-3.6.2";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/ca/38/16ba8d542e609997fdcd0214628421c971f8c395084085354b11ff4ac9c3/typing-3.6.2.tar.gz"; sha256 = "d514bd84b284dd3e844f0305ac07511f097e325171f6cc4a20878d11ad771849"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "https://docs.python.org/3/library/typing.html";
        license = licenses.psfl;
        description = "Type Hints for Python";
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



    "vine" = python.mkDerivation {
      name = "vine-1.1.4";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/32/23/36284986e011f3c130d802c3c66abd8f1aef371eae110ddf80c5ae22e1ff/vine-1.1.4.tar.gz"; sha256 = "52116d59bc45392af9fdd3b75ed98ae48a93e822cee21e5fda249105c59a7a72"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://github.com/celery/vine";
        license = licenses.bsdOriginal;
        description = "Promises, promises, promises.";
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



    "wmctrl" = python.mkDerivation {
      name = "wmctrl-0.3";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/01/c6/001aefbde5782d6f359af0a8782990c3f4e751e29518fbd59dc8dfc58b18/wmctrl-0.3.tar.gz"; sha256 = "d806f65ac1554366b6e31d29d7be2e8893996c0acbb2824bbf2b1f49cf628a13"; };
      doCheck = commonDoCheck;
      buildInputs = commonBuildInputs;
      propagatedBuildInputs = [ ];
      meta = with pkgs.stdenv.lib; {
        homepage = "http://bitbucket.org/antocuni/wmctrl";
        license = licenses.bsdOriginal;
        description = "A tool to programmatically control windows inside X";
      };
    };



    "yarl" = python.mkDerivation {
      name = "yarl-0.12.0";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/26/8b/e335a45600953cbaaa57e7f276eb8d89128898f11de63c47ecb97e32d29e/yarl-0.12.0.tar.gz"; sha256 = "fc0f71ffdce882b4d4b287b0b3a68d9f2557ab14cc2c10ce4df714c42512cbde"; };
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