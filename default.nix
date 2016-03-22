{ relengapi ? { outPath = ./.; name = "relengapi-src"; }
, pkgs ? import (builtins.fetchTarball "https://github.com/NixOS/nixpkgs-channels/archive/954925771482b50493a24615c6e7e82e044a4fdf.tar.gz") {}

, pythonVersion ? "python27Packages"
, ldap ? true
, develop ? true
}:

let

  pythonPackages = builtins.getAttr pythonVersion pkgs;

  fromRequirements = requirementsFile: map
    (specification:
      let fullname = pkgs.lib.splitString "==" specification; in
      if builtins.length fullname != 2
        then builtins.abort ("\n\n" +
          ''
            Failed while trying to parse `${specification}`

            Specification should include `==`.
          '')
        else
          let name = builtins.elemAt fullname 0; in
          if ! (builtins.hasAttr name self)
            then builtins.abort ("\n\n" +
              ''
                Package `${name}` could not be found in default.nix.
                Please make sure package exists.
              '')
            else
              let version = builtins.elemAt fullname 1;
                  pkg = builtins.getAttr name self;
                  pkg_version = pkgs.lib.getVersion pkg; in
              if (version != pkg_version)
                then builtins.abort ("\n\n" +
                  ''
                    Package `${name}` package defined in default.nix,
                    but version found (`${pkg_version}) does not match expected version (`${version}`)

                    Please make sure that default.nix file defines the same version as requirements file.
                  '')
                else pkg
        )
    (pkgs.lib.splitString "\n" (pkgs.lib.removeSuffix "\n" (builtins.readFile requirementsFile)));

  buildPythonPackage = { name, version, md5 ? "", deps ? [], ... } @ args:
    pythonPackages.buildPythonPackage ({
        name = "${name}-${version}";
        src = pkgs.fetchurl {
          inherit md5;
          url = "https://pypi.python.org/packages/source/${builtins.substring 0 1 name}/${name}/${name}-${version}.tar.gz";
        };
        propagatedBuildInputs = deps;
        doCheck = false;
      } // pkgs.lib.filterAttrs (n: v: !(builtins.elem n [ "name" "version" "md5" "deps" ])) args);

  self = builtins.listToAttrs (map (x: { name = x.name; value = buildPythonPackage x; }) [
    { name = "Babel";
      version = "2.2.0";
      md5 = "1b69e4b2ab3795119266ccaa36b36f15";
      deps = with self; [ pytz ];
      }
    { name = "Flask-BrowserID";
      version = "0.0.4";
      md5 = "931cfcb3bcb57c4c4431281388c4b6e9";
      deps = with self; [ Flask Flask-Login requests ];
      }
    { name = "Flask-Login";
      version = "0.3.2";
      md5 = "d95c2275d3e1c755145910077366dc45";
      deps = with self; [ Flask ];
      }
    { name = "Flask";
      version = "0.10.1";
      md5 = "378670fe456957eb3c27ddaef60b2b24";
      deps = with self; [ itsdangerous Werkzeug Jinja2 ];
      }
    { name = "IPy";
      version = "0.83";
      md5 = "7b8c6eb4111b15aea31b67108e769712";
      }
    { name = "Jinja2";
      version = "2.8";
      md5 = "edb51693fe22c53cee5403775c71a99e";
      deps = with self; [ MarkupSafe ];
      }
    { name = "Mako";
      version = "1.0.4";
      md5 = "c5fc31a323dd4990683d2f2da02d4e20";
      deps = with self; [ MarkupSafe ];
      }
    { name = "MarkupSafe";
      version = "0.23";
      md5 = "f5ab3deee4c37cd6a922fb81e730da6e";
      }
    { name = "MySQL-python";
      version = "1.2.5";
      deps = [ pkgs.mysql.lib pkgs.zlib ];
      src = pkgs.fetchzip { url = "https://pypi.python.org/packages/source/M/MySQL-python/MySQL-python-1.2.5.zip";
                            md5 = "2254ceca5992cb73ffa42fa7f0f07f45";
                            };
      }
    { name = "Pygments";
      version = "2.1.3";
      md5 = "ed3fba2467c8afcda4d317e4ef2c6150";
      deps = with self; [ docutils ];
      }
    { name = "SQLAlchemy";
      version = "1.0.12";
      md5 = "6d19ef29883bbebdcac6613cf391cac4";
      }
    { name = "Sphinx";
      version = "1.3.6";
      md5 = "7df638f47749f9284889c93012ffa07f";
      deps = with self; [ docutils Jinja2 Pygments sphinx_rtd_theme alabaster Babel snowballstemmer six nose ];
      }
    { name = "WSME";
      version = "0.7.0";
      md5 = "0d50fffead72d8a9fcb6152082d5b61b";
      deps = with self; [ pbr six simplegeneric netaddr pytz WebOb ];
      }
    { name = "WebOb";
      version = "1.6.0";
      md5 = "089d7fc6745f175737800237c7287802";
      }
    { name = "Werkzeug";
      version = "0.11.4";
      md5 = "9c5cfb704e39aea1524777caa5891eb0";
      deps = with self; [ itsdangerous ];
      }
    { name = "alabaster";
      version = "0.7.7";
      md5 = "957c665d7126dea8121f98038debcba7";
      deps = with self; [ Pygments ];
      }
    { name = "alembic";
      version = "0.8.5";
      md5 = "0a8b7ad897b35102c750f359e7ca633d";
      deps = with self; [ Mako SQLAlchemy python-editor ];
      }
    { name = "amqp";
      version = "1.4.9";
      md5 = "df57dde763ba2dea25b3fa92dfe43c19";
      }
    { name = "anyjson";
      version = "0.3.3";
      md5 = "2ea28d6ec311aeeebaf993cb3008b27c";
      }
    { name = "billiard";
      version = "3.3.0.23";
      md5 = "6ee416e1e7c8d8164ce29d7377cca6a4";
      }
    { name = "blinker";
      version = "1.4";
      md5 = "8b3722381f83c2813c52de3016b68d33";
      }
    { name = "boto";
      version = "2.39.0";
      md5 = "503e6ffd7d56dcdffa38cb316bb119e9";
      deps = with self; [ requests httpretty ];
      }
    { name = "bzrest";
      version = "1.1";
      md5 = "bbccd27404a6ece9d934ac1d7acc1e6a";
      deps = with self; [ requests ];
      }
    { name = "celery";
      version = "3.1.23";
      md5 = "c6f10f956a49424d553ab1391ab39ab2";
      deps = with self; [ kombu billiard pytz anyjson amqp ];
      }
    { name = "codecov";
      version = "1.6.3";
      md5 = "261bb39395131179e306a041b764d74d";
      deps = with self; [ requests coverage ];
      }
    { name = "coverage";
      version = "4.0.3";
      md5 = "c7d3db1882484022c81bf619be7b6365";
      }
    { name = "croniter";
      version = "0.3.12";
      md5 = "7c3690bb66ff53d91de7f41c52491d4b";
      deps = with self; [ python-dateutil ];
      }
    { name = "decorator";
      version = "4.0.6";
      md5 = "b17bfa17c294d33022a89de0f61d38fe";
      }
    { name = "docutils";
      version = "0.12";
      md5 = "4622263b62c5c771c03502afa3157768";
      }
    { name = "elasticache-auto-discovery";
      version = "0.0.5.1";
      md5 = "214f07aee9e195c24a43d95a5379c188";
      }
    { name = "funcparserlib";
      version = "0.3.6";
      md5 = "3aba546bdad5d0826596910551ce37c0";
      }
    { name = "funcsigs";
      version = "0.4";
      md5 = "fb1d031f284233e09701f6db1281c2a5";
      }
    { name = "furl";
      version = "0.4.92";
      md5 = "c6304750cba9db15ecbdea034a80e221";
      deps = with self; [ six orderedmultidict ];
      }
    { name = "futures";
      version = "3.0.5";
      md5 = "ced2c365e518242512d7a398b515ff95";
      }
    { name = "httpretty";
      version = "0.8.10";
      md5 = "9c130b16726cbf85159574ae5761bce7";
      }
    { name = "ipdb";
      version = "0.8.1";
      md5 = "IGNORED";
      deps = with self; [ ipython ];
      src = pkgs.fetchurl { url = "http://pypi.python.org/packages/source/i/ipdb/ipdb-0.8.1.zip";
                            md5 = "dbaded677eae99ed391fccc83e737c4f";
                            };
      }
    { name = "ipython";
      version = "4.0.3";
      md5 = "16d4c8e79510ba427fb5336e15b0ea34";
      deps =
        (with self; [ decorator pickleshare simplegeneric traitlets requests pexpect ]) ++
        (with pythonPackages.python.modules; [ readline sqlite3 ]);
      LC_ALL="en_US.UTF-8";
      buildInputs = with self; [ nose pkgs.glibcLocales Pygments mock ];
      patchPhase = ''
        sed -i -e "s|'\:sys_platform \=\= \"darwin\" and platform_python_implementation \=\= \"CPython\"': \['gnureadline'\],||" setup.py
      '';
      }
    { name = "ipython_genutils";
      version = "0.1.0";
      md5 = "9a8afbe0978adbcbfcb3b35b2d015a56";
      }
    { name = "isort";
      version = "4.2.2";
      md5 = "b6874ebe5c39fd3afdf8a0834c0fa9a2";
      }
    { name = "itsdangerous";
      version = "0.24";
      md5 = "a3d55aa79369aef5345c036a8a26307f";
      }
    { name = "kombu";
      version = "3.0.34";
      md5 = "2d7b5ab949c77aff1eb858c0ede11195";
      deps = with self; [ amqp anyjson ];
      }
    { name = "mock";
      version = "1.3.0";
      md5 = "73ee8a4afb3ff4da1b4afa287f39fdeb";
      deps = with self; [ funcsigs six pbr ];
      }
    { name = "mockcache";
      version = "1.0.3";
      md5 = "18e266040d9203117daad327bd4a3826";
      }
    { name = "mockldap";
      version = "0.2.6";
      md5 = "6bbe29f946b56ca383e2570c8252aac4";
      deps = with self; [ python-ldap funcparserlib mock ];
      }
    { name = "mohawk";
      version = "0.3.2.1";
      md5 = "733d2ef982fb6140cd656062a80cf331";
      deps = with self; [ six ];
      }
    { name = "moto";
      version = "0.4.23";
      md5 = "c0fd3aaaf758680c0204334fcb381991";
      deps = with self; [ Jinja2 boto Flask httpretty requests xmltodict six Werkzeug ];
      }
    { name = "mozdef_client";
      version = "1.0.6";
      md5 = "f94add7200cb6acf5cc4134f44fecf1e";
      deps = with self; [ requests-futures pytz boto ];
      }
    { name = "netaddr";
      version = "0.7.18";
      md5 = "c65bb34f8bedfbbca0b316c490cd13a0";
      }
    { name = "nose";
      version = "1.3.7";
      md5 = "4d3ad0ff07b61373d2cefc89c5d0b20b";
      deps = with self; [ coverage ];
      }
    { name = "orderedmultidict";
      version = "0.7.5";
      md5 = "721b0454c088f4f72b22d10cb5f1a2d0";
      deps = with self; [ six ];
      }
    { name = "path.py";
      version = "8.1.2";
      md5 = "31d07ac861284f8148a9041064852371";
      deps = with self; [ setuptools_scm ];
      }
    { name = "pbr";
      version = "1.8.1";
      md5 = "c8f9285e1a4ca6f9654c529b158baa3a";
      }
    { name = "pep8";
      version = "1.7.0";
      md5 = "2b03109b0618afe3b04b3e63b334ac9d";
      }
    { name = "pexpect";
      version = "3.3";
      md5 = "0de72541d3f1374b795472fed841dce8";
      }
    { name = "pickleshare";
      version = "0.6";
      md5 = "7fadddce8b1b0110c4ef905be795001a";
      deps = [ self."path.py" ];
      }
    { name = "pyflakes";
      version = "1.1.0";
      md5 = "e0bf854cd5abd4527e149692925b82eb";
      }
    { name = "python-dateutil";
      version = "2.5.1";
      md5 = "2769f13c596427558136b34977a95269";
      deps = with self; [ six ];
      }
    { name = "python-editor";
      version = "0.5";
      md5 = "ece4f1848d93286d58df88e3fcb37704";
      }
    { name = "python-ldap";
      version = "2.4.25";
      md5 = "21523bf21dbe566e0259030f66f7a487";
      deps = [ pkgs.openldap pkgs.cyrus_sasl pkgs.openssl ];
      NIX_CFLAGS_COMPILE = "-I${pkgs.cyrus_sasl}/include/sasl";
      }
    { name = "python-memcached";
      version = "1.57";
      md5 = "de21f64b42b2d961f3d4ad7beb5468a1";
      deps = with self; [ six ];
      }
    { name = "pytz";
      version = "2016.2";
      md5 = "18b3c555232aa8c9319d84871c453728";
      }
    { name = "redo";
      version = "1.5";
      md5 = "a18057787e969ee6aa7ccd88e5090762";
      }
    { name = "requests-futures";
      version = "0.9.7";
      md5 = "e26d2af8099b3235d696620dcb02a75b";
      deps = with self; [ requests futures ];
      }
    { name = "requests";
      version = "2.9.1";
      md5 = "0b7f480d19012ec52bab78292efd976d";
      }
    { name = "setuptools_scm";
      version = "1.10.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/source/s/setuptools_scm/setuptools_scm-1.10.1.tar.bz2"; 
                            md5 = "99823e2cd564b996f18820a065f0a974";
                            };
      preBuild = "${pythonPackages.python.interpreter} setup.py egg_info";
      }
    { name = "simplegeneric";
      version = "0.8.1";
      src = pkgs.fetchurl { url = "https://pypi.python.org/packages/source/s/simplegeneric/simplegeneric-0.8.1.zip";
                            md5 = "f9c1fab00fd981be588fc32759f474e3";
                            };
      }
    { name = "simplejson";
      version = "3.8.2";
      md5 = "53b1371bbf883b129a12d594a97e9a18";
      }
    { name = "six";
      version = "1.10.0";
      md5 = "34eed507548117b2ab523ab14b2f8b55";
      }
    { name = "slugid";
      version = "1.0.7";
      md5 = "2af844a4dd0d33c9638c473c78d3a0da";
      }
    { name = "snowballstemmer";
      version = "1.2.1";
      md5 = "643b019667a708a922172e33a99bf2fa";
      }
    { name = "sphinx_rtd_theme";
      version = "0.1.9";
      md5 = "86a25c8d47147c872e42dc84cc66f97b";
      postPatch = ''
        rm requirements.txt
        touch requirements.txt
      '';
      }
    { name = "structlog";
      version = "16.0.0";
      md5 = "59ac00a23b966c6d63ad85c26f454ea9";
      deps = with self; [ six ];
      }
    { name = "taskcluster";
      version = "0.2.0";
      md5 = "3ba660ad738841b7f30a2a36e9873eb9";
      deps = with self; [ mohawk requests six slugid ];
      }
    { name = "traitlets";
      version = "4.1.0";
      md5 = "2ebf5e11a19f82f25395b4a793097080";
      deps = with self; [ ipython_genutils decorator ];
      }
    { name = "wrapt";
      version = "1.10.6";
      md5 = "e29294a8949ff4dc74d6fcd800f6f23d";
      }
    { name = "xmltodict";
      version = "0.10.1";
      md5 = "cb538f606811d9e8d108fd15675b492f";
      }
  ]);

  version = pkgs.lib.removeSuffix "\n" (builtins.head (pkgs.lib.splitString "\n" (builtins.readFile ./VERSION)));

in pythonPackages.buildPythonPackage rec {
  name = "relengapi-${version}";
  src = relengapi;
  # TODO: read from requirements-dev.txt
  buildInputs =
    (fromRequirements ./requirements-test.txt)
    ++ (builtins.attrValues pythonPackages.python.modules)
    ++ (pkgs.lib.optionals develop (with self; [
      ipdb
    ]));
  # TODO: read from requirements.txt
  propagatedBuildInputs = 
    (fromRequirements ./requirements.txt)
    ++ pkgs.lib.optionals ldap (fromRequirements ./requirements-ldap.txt);
  doCheck = false;  # TODO: skip tests for now since they dont run in nix's restricted env
  checkPhase = ''
    export RELENGAPI_SETTINGS=settings_example.py
    export VIRTUAL_ENV=something
    export PATH=$out/bin:$PATH
    sh ./validate.sh
  '';
  postShellHook = ''
    export RELENGAPI_SETTINGS=`pwd`/settings.py
  '';
}
