{ releng_pkgs }: 

let

  inherit (builtins) readFile concatStringsSep;
  inherit (releng_pkgs) from_requirements;
  inherit (releng_pkgs.pkgs) makeWrapper;
  inherit (releng_pkgs.pkgs.lib) removeSuffix inNixShell;

  python = import ./requirements.nix {
    inherit (releng_pkgs) pkgs;
  };

  version = removeSuffix "\n" (readFile ./VERSION);

  srcs = [
    "./../relengapi_common"
    "./../relengapi_clobberer"
  ];

  self = python.mkDerivation {
     namePrefix = "";
     name = "relengapi_clobberer-${version}";
     srcs = if inNixShell then null else (map (x: ./. + ("/" + x)) srcs);
     sourceRoot = ".";
     buildInputs = [ makeWrapper ] ++
       from_requirements [ ./requirements-dev.txt
                           ./requirements-setup.txt ] python.packages;
     propagatedBuildInputs =
       from_requirements [ ./../relengapi_common/requirements.txt
                           ./requirements.txt
                           ./requirements-prod.txt ] python.packages;
     postInstall = ''
       mkdir -p $out/bin $out/etc

       ln -s ${python.interpreter.interpreter} $out/bin
       ln -s ${python.packages."gunicorn"}/bin/gunicorn $out/bin
       ln -s ${python.packages."newrelic"}/bin/newrelic-admin $out/bin
   
       cp ./src-*-relengapi_clobberer/settings.py $out/etc

       for i in $out/bin/*; do
         wrapProgram $i --set PYTHONPATH $PYTHONPATH
       done
     '';
     checkPhase = ''
       flake8 settings.py setup.py relengapi_clobberer/
       # TODO: pytest relengapi_clobberer/
     '';
     shellHook = ''
       export CACHE_DEFAULT_TIMEOUT=3600
       export CACHE_TYPE=filesystem
       export CACHE_DIR=$PWD/cache
       export DATABASE_URL=sqlite:///$PWD/app.db

       for i in ${concatStringsSep " " srcs}; do
         if test -e $i/setup.py; then
           pushd $i >> /dev/null
           tmp_path=$(mktemp -d)
           export PATH="$tmp_path/bin:$PATH"
           export PYTHONPATH="$tmp_path/${python.__old.python.sitePackages}:$PYTHONPATH"
           mkdir -p $tmp_path/${python.__old.python.sitePackages}
           ${python.__old.bootstrapped-pip}/bin/pip install -q -e . --prefix $tmp_path
           popd >> /dev/null
         fi
       done
     '';
     passthru.python = python;
     passthru.dockerEnvs = [
       "APP_SETTINGS=${self}/etc/settings.py"
     ];
     passthru.dockerConfig = {
       Cmd = [
         "newrelic-admin" "run-program"
           "gunicorn" "relengapi_clobberer:app"
             "--timeout" "300" "--log-file" "-"
       ];
     };
   };
in self
