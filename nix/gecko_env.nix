{ releng_pkgs }:

let
  inherit (releng_pkgs.pkgs) rustStable clang-tools xorg bash xlibs autoconf213 clang llvm llvmPackages;
  inherit (releng_pkgs.mozilla) gecko;

in gecko.overrideDerivation (old: {
  # Dummy src, cannot be null
  src = ./.;
  configurePhase = ''
    mkdir -p $out/bin
    mkdir -p $out/conf
  '';
  buildPhase = ''

    # Gecko build environment
    geckoenv=$out/bin/gecko-env

    echo "#!${bash}/bin/sh" > $geckoenv
    echo "export SHELL=xterm" >> $geckoenv
    env | grep -E '^(PATH|PKG_CONFIG_PATH|CMAKE_INCLUDE_PATH)='| sed 's/^/export /' >> $geckoenv
    echo "export CPLUS_INCLUDE_PATH=$CMAKE_INCLUDE_PATH:\$EXTRAS_INCLUDE_PATH" >> $geckoenv
    echo "export C_INCLUDE_PATH=$CMAKE_INCLUDE_PATH:\$EXTRAS_INCLUDE_PATH" >> $geckoenv
    echo "export INCLUDE_PATH=$CMAKE_INCLUDE_PATH:\$EXTRAS_INCLUDE_PATH" >> $geckoenv

    # Add self in PATH, needed to exec
    echo "export PATH=$out/bin:\$PATH" >> $geckoenv

    # Use python2.7 environment
    echo "export PYTHONPATH=$PYTHONPATH" >> $geckoenv

    # Build LDFLAGS and LIBRARY_PATH
    echo "export LDFLAGS=\"$NIX_LDFLAGS\"" >> $geckoenv
    echo "export LIBRARY_PATH=\"$CMAKE_LIBRARY_PATH\"" >> $geckoenv
    echo "export LD_LIBRARY_PATH=\"$CMAKE_LIBRARY_PATH\"" >> $geckoenv

    # Setup Clang & Autoconf
    echo "export CC=${clang}/bin/clang" >> $geckoenv
    echo "export CXX=${clang}/bin/clang++" >> $geckoenv
    echo "export LD=${clang}/bin/ld" >> $geckoenv
    echo "export LLVM_CONFIG=${llvm}/bin/llvm-config" >> $geckoenv
    echo "export LLVMCONFIG=${llvm}/bin/llvm-config" >> $geckoenv # we need both
    echo "export AUTOCONF=${autoconf213}/bin/autoconf" >> $geckoenv

    # Build custom mozconfig
    mozconfig=$out/conf/mozconfig
    echo > $mozconfig "
    ac_add_options --enable-clang-plugin
    ac_add_options --with-clang-path=${clang}/bin/clang
    ac_add_options --with-libclang-path=${llvmPackages.clang-unwrapped}/lib
    "
    echo "export MOZCONFIG=$mozconfig" >> $geckoenv

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
      # Use clang as compiler
      clang

      # Update rust to 1.17
      rustStable.rustc
      rustStable.cargo
    ];
})
