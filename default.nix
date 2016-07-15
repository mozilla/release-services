{}:

let
  pkgs = import <nixpkgs> {};
  version = "1.0.0";
in pkgs.stdenv.mkDerivation {
  name = "relengapi-${version}";
  buildInputs = with pkgs; [
    pythonPackages.virtualenv
    libxslt
    libxml2
    zlib
    libffi
    openssl
    postgresql
    nodejs-6_x
    phantomjs2
    sassc
    mysql.lib
    zlib
    openssl
    elmPackages.elm
  ];
  shellHook = ''
    export CACHE_DEFAULT_TIMEOUT=3600
    export CACHE_TYPE=filesystem
    export CACHE_DIR=$TMPDIR/clobberer
    export DATABASE_URL=sqlite:///$PWD/app.db
    export PATH=$PWD/src/relengapi_tools//node_modules/.bin:$PATH
  '';
}
