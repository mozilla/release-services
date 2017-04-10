{ releng_pkgs }:

let
  inherit (releng_pkgs.pkgs) rustStable clang-tools gcc xorg bash xlibs autoconf213;
  inherit (releng_pkgs.mozilla) gecko;

in gecko.overrideDerivation (old: {
  # Dummy src, cannot be null
  src = ./.;
  configurePhase = ''
    mkdir -p $out/bin
  '';
  buildPhase = ''

    # Gecko build environment
    geckoenv=$out/bin/gecko-env

    echo "#!${bash}/bin/sh" > $geckoenv
    echo "export SHELL=xterm" >> $geckoenv
    env | grep -E '^(PATH|PKG_CONFIG_PATH|CMAKE_INCLUDE_PATH)='| sed 's/^/export /' >> $geckoenv
    echo "export CPLUS_INCLUDE_PATH=$CMAKE_INCLUDE_PATH" >> $geckoenv
    echo "export C_INCLUDE_PATH=$CMAKE_INCLUDE_PATH" >> $geckoenv

    # Add self in PATH, needed to exec
    echo "export PATH=$out/bin:\$PATH" >> $geckoenv

    # Transform LDFLAGS in list of paths for LIBRARY_PATH
    ldflags=$(env | grep -e '^NIX_LDFLAGS=' | cut -c13-)
    echo "export LIBRARY_PATH=$(echo $ldflags | sed -E 's,-rpath ([/\.a-zA-Z0-9\-]+) ,,g' | sed -E 's, -L(\s*),:,g')" >> $geckoenv

    # Setup CC & Autoconf
    echo "export CC=${gcc}/bin/gcc" >> $geckoenv
    echo "export CXX=${gcc}/bin/g++" >> $geckoenv
    echo "export AUTOCONF=${autoconf213}/bin/autoconf" >> $geckoenv

    # Exec command line from arguments
    echo "set -x" >> $geckoenv
    echo "exec \$@" >> $geckoenv

    chmod +x $geckoenv
  '';
  installPhase = ''
    echo "Skip install"
  '';
  propagatedBuildInputs = old.propagatedBuildInputs
    ++ [

      # Update rust to 1.15
      rustStable.rustc
      rustStable.cargo
    ];
})
