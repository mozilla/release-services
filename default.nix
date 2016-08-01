{ pkgs ? import (builtins.fetchTarball "https://github.com/garbas/nixpkgs/archive/9d1bd64f43cacd72f1c6aaeeb333e3618a838524.tar.gz") {}
, version ? pkgs.lib.removeSuffix "\n" (builtins.readFile ./VERSION)
}:

let
  python = import ./requirements.nix { inherit pkgs; };
  from_requirements = files:
    map
      (requirement: builtins.getAttr requirement python.pkgs)
      (pkgs.lib.unique
        (builtins.filter
          (x: x != "")
          (pkgs.lib.flatten
            (map
              (file: pkgs.lib.splitString "\n"(pkgs.lib.removeSuffix "\n" (builtins.readFile file)))
              files
            )
          )
        )
      );
  srcs = [
    "./src/relengapi_common"
    "./src/relengapi_clobberer"
  ];

in python.mkDerivation {
  name = "relengapi-${version}";
  tracePhases = true;
  srcs = if pkgs.lib.inNixShell then null else [ ./src/relengapi_common
                                                 ./src/relengapi_clobberer
                                               ];
  buildInputs = builtins.filter (x: ! builtins.isFunction x) (builtins.attrValues python.pkgs);
  propagatedBuildInputs = from_requirements [ ./src/relengapi_common/requirements.txt
                                              ./src/relengapi_clobberer/requirements.txt
                                            ];
  patchPhase = ''
    for i in ./*; do
      if [ -d $i ]; then
        rm -f $i/VERSION
        echo ${version} > $i/VERSION
      fi
    done
  '';
  shellHook = ''
    alias python=`which python3`

    export CACHE_DEFAULT_TIMEOUT=3600
    export CACHE_TYPE=filesystem
    export CACHE_DIR=$TMPDIR/clobberer
    export DATABASE_URL=sqlite:///$PWD/app.db
    export PATH=$PWD/src/relengapi_tools//node_modules/.bin:$PATH

    for i in ${builtins.concatStringsSep " " srcs}; do
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
}
