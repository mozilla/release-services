{ releng_pkgs }:

let
  inherit (releng_pkgs.pkgs) rustChannels bash autoconf213 clang_4 llvm_4 llvmPackages_4;
  inherit (releng_pkgs.pkgs.devEnv) gecko;

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

    # Clean python environment
    echo "export PYTHONPATH=" >> $geckoenv

    # Build LDFLAGS and LIBRARY_PATH
    echo "export LDFLAGS=\"$NIX_LDFLAGS\"" >> $geckoenv
    echo "export LIBRARY_PATH=\"$CMAKE_LIBRARY_PATH\"" >> $geckoenv
    echo "export LD_LIBRARY_PATH=\"$CMAKE_LIBRARY_PATH\"" >> $geckoenv

    # Setup Clang & Autoconf
    echo "export CC=${clang_4}/bin/clang" >> $geckoenv
    echo "export CXX=${clang_4}/bin/clang++" >> $geckoenv
    echo "export LD=${clang_4}/bin/ld" >> $geckoenv
    echo "export LLVM_CONFIG=${llvm_4}/bin/llvm-config" >> $geckoenv
    echo "export LLVMCONFIG=${llvm_4}/bin/llvm-config" >> $geckoenv # we need both
    echo "export AUTOCONF=${autoconf213}/bin/autoconf" >> $geckoenv

    # Build custom mozconfig
    mozconfig=$out/conf/mozconfig
    echo > $mozconfig "
    ac_add_options --enable-clang-plugin
    ac_add_options --with-clang-path=${clang_4}/bin/clang
    ac_add_options --with-libclang-path=${llvmPackages_4.libclang}/lib
    "
    echo "export CLANG_MOZCONFIG=$mozconfig" >> $geckoenv

    # Use updated rust version
    echo "export PATH=${rustChannels.stable.rust}/bin:${rustChannels.stable.cargo}/bin:\$PATH" >> $geckoenv
  '';
  installPhase = ''
    geckoenv=$out/bin/gecko-env

    # Exec command line from arguments
    echo "set -x" >> $geckoenv
    echo "exec \$@" >> $geckoenv

    chmod +x $geckoenv
  '';
  propagatedBuildInputs = old.propagatedBuildInputs
    ++ [
      # Update rust to latest stable
      rustChannels.stable.rust
      rustChannels.stable.cargo
    ];
})
