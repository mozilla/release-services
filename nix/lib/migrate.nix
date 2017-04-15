{ releng_pkgs }: 

let

  inherit (releng_pkgs.tools)
    mysql2pgsql;
  inherit (releng_pkgs.pkgs)
    bash
    coreutils
    gnused
    gnugrep
    mysql
    openssh
    postgresql
    writeScriptBin;

in {

  mysql2postgresql =
    { name
    , beforeSQL ? ""
    , afterSQL ? ""
    , config ? ""
    }:
    writeScriptBin "migrate" ''
      #${bash}/bin/bash -e


      ## parse cli arguments

      CLI_SERVER=$1
      CLI_MYSQL=$2
      CLI_POSTGRESQL=$3

      if [[ -z "$CLI_SERVER" ]] ||
         [[ -z "$CLI_MYSQL" ]] ||
         [[ -z "$CLI_POSTGRESQL" ]]; then
         echo ""
         echo "You need to provide (in order) "
         echo " - 'username@hostname' to connect to ssh tunneling server"
         echo " - database connection string of source mysql server"
         echo " - database connection string of targer postgresql server"
         echo ""
         exit 1
      fi



      ## helper functions 

      parse_url() {
        eval $(echo "$2" | ${gnused}/bin/sed -e "s#^\(\(.*\)://\)\?\(\([^:@]*\)\(:\(.*\)\)\?@\)\?\([^/?]*\)\(/\(.*\)\)\?#$1SCHEME='\2' $1USER='\4' $1PASSWORD='\6' $1HOST='\7' $1DATABASE='\9'#")
        host=$1HOST
        host=''${!host}
        if [[ $host == *":"* ]]; then
          eval "$1PORT=`echo $host |cut -d':' -f2`
          eval "$1HOST=`echo $host |cut -d':' -f1`
        fi
      }



      ## parse & validate $CLI_SERVER variable

      parse_url "SERVER_" "$CLI_SERVER"

      if [[ -z "$SERVER_USER" ]] ||
         [[ -z "$SERVER_HOST" ]]; then
         echo "ERROR"
         echo ""
         echo "First argument does not provide 'username' and 'host' of tunneling server."
         echo ""
         echo "We got:"
         echo "  $CLI_SERVER"
         echo "Expecting:"
         echo "  <username>@<hostname>"
         echo ""
         exit 1
      fi



      ## parse & validate $CLI_MYSQL variable

      parse_url "MYSQL_" "$CLI_MYSQL"

      if [[ -z "$MYSQL_PORT" ]]; then MYSQL_PORT=3306; fi

      if [[ "$MYSQL_SCHEME" != "mysql" ]] ||
         [[ -z "$MYSQL_USER" ]] ||
         [[ -z "$MYSQL_PASSWORD" ]] ||
         [[ -z "$MYSQL_HOST" ]] ||
         [[ -z "$MYSQL_PORT" ]] ||
         [[ -z "$MYSQL_DATABASE" ]]; then
         echo "ERROR"
         echo ""
         echo "Second argument does not provide correct database connection string for mysql server."
         echo ""
         echo "We got:"
         echo "  $CLI_MYSQL"
         echo "Expecting:"
         echo "  mysql://<username>:<password>@<hostname>:<port>/<database>"
         echo ""
         exit 1
      fi



      ## parse & validate $CLI_POSTGRESQL variable

      parse_url "POSTGRESQL_" "$CLI_POSTGRESQL"

      if [[ -z "$POSTGRESQL_PORT" ]]; then POSTGRESQL_PORT=5432; fi

      if [[ "$POSTGRESQL_SCHEME" != "postgres" ]] ||
         [[ -z "$POSTGRESQL_USER" ]] ||
         [[ -z "$POSTGRESQL_PASSWORD" ]] ||
         [[ -z "$POSTGRESQL_HOST" ]] ||
         [[ -z "$POSTGRESQL_PORT" ]] ||
         [[ -z "$POSTGRESQL_DATABASE" ]]; then
         echo "ERROR"
         echo ""
         echo "Third argument does not provide correct database connection string for mysql server."
         echo ""
         echo "We got:"
         echo "  $CLI_POSTGRESQL"
         echo "Expecting:"
         echo "  postgres://<username>:<password>@<hostname>:<port>/<database>"
         echo ""
         exit 1
      fi



      ## create temporary directory and random mysql port on localhost

      MYSQL2PGSQL_TMPDIR=`${coreutils}/bin/mktemp -d -t "migrate-${name}-XXXXX"`
      MYSQL2PGSQL_YML=$MYSQL2PGSQL_TMPDIR/mysql2pgsql.yml
      MYSQL_LOCAL_PORT=`${coreutils}/bin/shuf -i 10000-65000 -n 1`



      ## create mysql2pgsql configuration file
      # more about mysql2psql.yml here https://github.com/philipsoutham/py-mysql2pgsql

      ${coreutils}/bin/cat > $MYSQL2PGSQL_YML <<EOL
      mysql:
        hostname: 127.0.0.1
        port: $MYSQL_LOCAL_PORT
        username: $MYSQL_USER
        password: $MYSQL_PASSWORD
        database: $MYSQL_DATABASE
        compress: false
      destination:
        file:
        postgres:
          hostname: $POSTGRESQL_HOST
          port: $POSTGRESQL_PORT
          username: $POSTGRESQL_USER
          password: $POSTGRESQL_PASSWORD
          database: $POSTGRESQL_DATABASE
      ${config}
      EOL
      echo "====================================================="
      cat $MYSQL2PGSQL_YML
      echo "====================================================="



      ## open (automatically closing) shh tunnel

      ${openssh}/bin/ssh -f \
          -o ExitOnForwardFailure=yes \
          -L $MYSQL_LOCAL_PORT:$MYSQL_HOST:$MYSQL_PORT $SERVER_USER@$SERVER_HOST \
          sleep 10


      ## test connection with mysql

      ${mysql}/bin/mysql \
        -e 'SHOW DATABASES;' \
        -h 127.0.0.1 -P $MYSQL_LOCAL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE


      ## run beforeSQL query on postgresql (this also tests the connection)

      PGPASSWORD=$POSTGRESQL_PASSWORD \
        ${postgresql}/bin/psql -c "${beforeSQL}" \
        -U $POSTGRESQL_USER -w -h $POSTGRESQL_HOST -p $POSTGRESQL_PORT $POSTGRESQL_DATABASE


      ## sync the databases

      ${mysql2pgsql}/bin/py-mysql2pgsql -v -f $MYSQL2PGSQL_YML



      ## run afterSQL query on postgresql

      PGPASSWORD=$POSTGRESQL_PASSWORD \
        ${postgresql}/bin/psql -c "${afterSQL}" \
        -U $POSTGRESQL_USER -w -h $POSTGRESQL_HOST -p $POSTGRESQL_PORT $POSTGRESQL_DATABASE


      ## remove temporary folder

      rm -rf $MYSQL2PGSQL_TMPDIR
    '';

}
