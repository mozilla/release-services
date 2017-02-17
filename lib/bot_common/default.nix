{ releng_pkgs, python, extras }:

let

  inherit (releng_pkgs.pkgs.lib) fileContents optionals;
  inherit (releng_pkgs.lib) filterSource;

  version = fileContents ./../../VERSION;
  name = "bot-common";

in python.mkDerivation {
  name = "${name}-${version}";
  src = filterSource ./. { inherit name; };
  buildInputs =
    [ python.packages."flake8"
      python.packages."pytest"
    ];
  propagatedBuildInputs =
    []
     ++ optionals (builtins.elem "pulse" extras) [ python.packages."aioamqp" ]
     ++ optionals (builtins.elem "taskcluster" extras) [ python.packages."taskcluster" ]
    ;
  checkPhase = ''
    flake8 --exclude=nix_run_setup.py,build/
    #pytest tests/
  '';
  patchPhase = ''
    rm VERSION
    echo ${version} > VERSION
  '';
  passthru.extras = extras;
}

