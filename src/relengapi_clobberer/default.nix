{ releng_pkgs }: 

let

  name = "relengapi_clobberer";

  inherit (builtins) readFile concatStringsSep;
  inherit (releng_pkgs.lib) fromRequirementsFile;
  inherit (releng_pkgs.tools) mysql2sqlite;
  inherit (releng_pkgs.pkgs) makeWrapper writeScriptBin bash coreutils openssh sqlite;
  inherit (releng_pkgs.pkgs.lib) removeSuffix inNixShell;

  python = import ./requirements.nix {
    inherit (releng_pkgs) pkgs;
  };

  version = removeSuffix "\n" (readFile ./VERSION);

  srcs = [
    "./../relengapi_common"
    "./../relengapi_clobberer"
  ];

  migrate_from_mysql_to_postgresql = writeScriptBin "migrate-from-mysql-to-postgresql" ''
    #${bash}/bin/bash -e
  '';
  migrate_from_mysql_to_sqlite = writeScriptBin "migrate-from-mysql-to-sqlite" ''
    #${bash}/bin/bash -e

    MIGRATE_USER=$1
    MIGRATE_DB_PASSWORD=$2
    MIGRATE_DB=$3

    if [[ -z "$MIGRATE_DB_PASSWORD" ]] ||
       [[ -s "$MIGRATE_USER" ]]; then
       echo "ERROR:"
       echo ""
       echo "You need to provide "
       echo " - username: to connect to 'relengwebadm.private.scl3.mozilla.com' server as first argument"
       echo " - password: for 'devtools-rw-vip.db.scl3.mozilla.com' mysql database"
       echo " - database: path to sqlite database file"
       echo ""
       exit 1
    fi

    MIGRATE_TMPDIR=`${coreutils}/bin/mktemp -d -t "migrate-${name}-XXXXX"`
    MIGRATE_DUMP="$MIGRATE_TMPDIR/dump.sql"
    MIGRATE_DUMP_TMP="$MIGRATE_DUMP.tmp"

    # administration server
    RELENGADM_URL="relengwebadm.private.scl3.mozilla.com"

    # XXX: maybe we need to make this configurable
    MYSQL_PRODUCTION_USER="clobberer2"
    MYSQL_PRODUCTION_URL="devtools-rw-vip.db.scl3.mozilla.com"
    MYSQL_PRODUCTION_DBNAME="clobberer"
    MYSQL_DUMP_TMP="mysqldump_${name}.sql"

    ${coreutils}/bin/rm -f $MIGRATE_DUMP $MIGRATE_DUMP_TMP

    ${sqlite.bin}/bin/sqlite3 $MIGRATE_DB "DROP TABLE IF EXISTS \`clobberer_builds\`;"
    ${sqlite.bin}/bin/sqlite3 $MIGRATE_DB "DROP TABLE IF EXISTS \`clobberer_times\`;"
    ${sqlite.bin}/bin/sqlite3 $MIGRATE_DB "DROP TABLE IF EXISTS \`builds\`;"
    ${sqlite.bin}/bin/sqlite3 $MIGRATE_DB "DROP TABLE IF EXISTS \`clobber_times\`;"

    ${openssh}/bin/ssh $MIGRATE_USER@$RELENGADM_URL "rm -f $MYSQL_DUMP_TMP && mysqldump --skip-extended-insert --compact -u $MYSQL_PRODUCTION_USER -p$MIGRATE_DB_PASSWORD -h $MYSQL_PRODUCTION_URL $MYSQL_PRODUCTION_DBNAME > $MYSQL_DUMP_TMP" 2> /dev/null
    ${openssh}/bin/scp $MIGRATE_USER@$RELENGADM_URL:$MYSQL_DUMP_TMP $MIGRATE_DUMP_TMP
    ${openssh}/bin/ssh $MIGRATE_USER@$RELENGADM_URL "rm $MYSQL_DUMP_TMP"

    ${coreutils}/bin/cat $MIGRATE_DUMP_TMP               >> $MIGRATE_DUMP

    ${mysql2sqlite}/bin/mysql2sqlite $MIGRATE_DUMP | ${sqlite.bin}/bin/sqlite3 $MIGRATE_DB

    ${sqlite.bin}/bin/sqlite3 $MIGRATE_DB "ALTER TABLE \`builds\` RENAME TO \`clobberer_builds\`;"
    ${sqlite.bin}/bin/sqlite3 $MIGRATE_DB "ALTER TABLE \`clobber_times\` RENAME TO \`clobberer_times\`;"

    rm -rf $MIGRATE_TMPDIR
  '';

  self = python.mkDerivation {
     namePrefix = "";
     name = "${name}-${version}";
     srcs = if inNixShell then null else (map (x: ./. + ("/" + x)) srcs);
     sourceRoot = ".";
     buildInputs = [ makeWrapper ] ++
       fromRequirementsFile [ ./requirements-dev.txt
                              ./requirements-setup.txt ] python.packages;
     propagatedBuildInputs =
       fromRequirementsFile [ ./../relengapi_common/requirements.txt
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
     passthru.migrate_from_mysql_to_sqlite = migrate_from_mysql_to_sqlite;
     passthru.migrate_from_mysql_to_postgresql = migrate_from_mysql_to_postgresql;
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
     passthru.updateSrc = releng_pkgs.pkgs.writeScriptBin "update" ''
       pushd src/relengapi_clobberer
       ${releng_pkgs.tools.pypi2nix}/bin/pypi2nix -v \
         -V 3.5 \
         -E "postgresql" \
         -r requirements.txt \
         -r requirements-setup.txt \
         -r requirements-dev.txt \
         -r requirements-prod.txt 
       popd
     '';
   };
in self
