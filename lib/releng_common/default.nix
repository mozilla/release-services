{ releng_pkgs, python, extras }:

let

  inherit (releng_pkgs.pkgs.lib) fileContents optionals;
  inherit (releng_pkgs.lib) filterSource;

  version = fileContents ./../../VERSION;
  name = "releng-common";

in python.mkDerivation {
  name = "${name}-${version}";
  src = filterSource ./. { inherit name; };
  buildInputs =
    [ python.packages."flake8"
      python.packages."pytest"
      python.packages."responses"
    ];
  propagatedBuildInputs =
    [ python.packages."Flask"
      python.packages."Jinja2"
      python.packages."gunicorn"
      python.packages."newrelic"
    ] ++ optionals (builtins.elem "cache" extras) [ python.packages."Flask-Cache" ]
      ++ optionals (builtins.elem "auth" extras) [ python.packages."Flask-Login" python.packages."taskcluster" ]
      ++ optionals (builtins.elem "api" extras) [ python.packages."connexion" ]
      ++ optionals (builtins.elem "log" extras) [
        python.packages."structlog"
        python.packages."Logbook"
      ]
      ++ optionals (builtins.elem "security" extras) [ python.packages."flask-talisman" ]
      ++ optionals (builtins.elem "cors" extras) [ python.packages."Flask-Cors" ]
      ++ optionals (builtins.elem "pulse" extras) [ python.packages."kombu" ]
      ++ optionals (builtins.elem "db" extras) [
        python.packages."psycopg2"
        python.packages."Flask-SQLAlchemy"
        python.packages."Flask-Migrate"
      ];
  checkPhase = ''
    flake8 --exclude=nix_run_setup.py,migrations/,build/
    #pytest tests/
  '';
  patchPhase = ''
    rm VERSION
    echo ${version} > VERSION
  '';
  passthru.extras = extras;
}
