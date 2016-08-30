{ releng_pkgs }: 

let

  inherit (builtins) readFile concatStringsSep;
  inherit (releng_pkgs.lib) fromRequirementsFile;
  inherit (releng_pkgs.pkgs) makeWrapper;
  inherit (releng_pkgs.pkgs.lib) removeSuffix inNixShell;

  name = "shipit_dashboard";
  version = removeSuffix "\n" (readFile ./VERSION);

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };

  srcs = [
    "./../releng_common"
    "./../${name}"
  ];

  self = python.mkDerivation {
    namePrefix = "";
    name = "${name}-${version}";
    srcs = if inNixShell then null else (map (x: ./. + ("/" + x)) srcs);
    sourceRoot = ".";
    buildInputs = [ makeWrapper ] ++
      fromRequirementsFile [ ./requirements-dev.txt
                             ./requirements-setup.txt ] python.packages;
    propagatedBuildInputs =
      fromRequirementsFile [ ./../releng_common/requirements.txt
                             ./requirements.txt
                             ./requirements-prod.txt ] python.packages;
    postInstall = ''
      mkdir -p $out/bin $out/etc

      ln -s ${python.interpreter.interpreter} $out/bin
      ln -s ${python.packages."Flask"}/bin/flask $out/bin
      ln -s ${python.packages."gunicorn"}/bin/gunicorn $out/bin
      ln -s ${python.packages."newrelic"}/bin/newrelic-admin $out/bin
   
      cp ./src-*-${name}/settings.py $out/etc

      for i in $out/bin/*; do
        wrapProgram $i --set PYTHONPATH $PYTHONPATH
      done
    '';
    checkPhase = ''
      flake8 settings.py setup.py ${name}/
      # TODO: pytest ${name}/
    '';
    shellHook = ''
      export CACHE_DEFAULT_TIMEOUT=3600
      export CACHE_TYPE=filesystem
      export CACHE_DIR=$PWD/cache
      export DATABASE_URL=sqlite:///$PWD/app.db

      for i in ${concatStringsSep " " srcs}; do
        if test -e src/''${i:5}/setup.py; then
          echo "Setting \"''${i:5}\" in development mode ..."
          pushd src/''${i:5} >> /dev/null
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
          "gunicorn" "${name}:app"
            "--timeout" "300" "--log-file" "-"
      ];
    };
    passthru.updateSrc = releng_pkgs.pkgs.writeScriptBin "update" ''
      pushd src/${name}
      ${releng_pkgs.tools.pypi2nix}/bin/pypi2nix -v \
       -V 3.5 \
       -E "postgresql libffi openssl" \
       -r requirements.txt \
       -r requirements-setup.txt \
       -r requirements-dev.txt \
       -r requirements-prod.txt 
      popd
    '';
   };
in self
