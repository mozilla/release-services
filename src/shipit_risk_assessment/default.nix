{ releng_pkgs 
}: 

let

  inherit (releng_pkgs.lib) mkPython mkTaskclusterHook fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript makeWrapper cacert fetchFromGitHub llvmPackages_4 llvm_4 sqlite autoconf213 clang_4 rustStable gcc-unwrapped glibc glibcLocales gcc;
  inherit (releng_pkgs.pkgs.lib) fileContents optional licenses importJSON ;
  inherit (releng_pkgs.tools) pypi2nix mercurial;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation ;
  inherit (releng_pkgs) gecko-env;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  name = "mozilla-shipit-risk-assessment";
  dirname = "shipit_risk_assessment";
  version = fileContents ./VERSION;

  gecko = gecko-env.overrideDerivation(old : {
    buildInputs = old.buildInputs ++ [
      llvm_4 # needed for llvm-config

      # TRASHME because of extra flags ?
      # May be needed in docker image (propagated) :/
      gcc-unwrapped
      glibc.dev
      glibc
      gcc
    ];
  });

  libmocoda = mkDerivation {
    name = "libmocoda-${version}";
    src = fetchFromGitHub (importJSON ./mocoda.json);
    buildInputs = [
      llvm_4
      llvmPackages_4.clang-unwrapped
      sqlite
    ];
    buildPhase = ''
      cd src
      export AUTOCONF="${autoconf213}/bin/autoconf"
      export CC="${clang_4}/bin/clang"
      export CXX="${clang_4}/bin/clang++"
      export LDFLAGS="-lsqlite3 -lclang -Wl,--as-needed"
      export INC=""
      make
    '';
    installPhase = ''
      mkdir -p $out/lib
      cp libmocoda.so $out/lib
  
      # Build mozconfig
      mkdir -p $out/conf
      echo > $out/conf/mozconfig "
      CC=\"${clang_4}/bin/clang -fplugin=$out/lib/libmocoda.so\"
      CXX=\"${clang_4}/bin/clang++ -fplugin=$out/lib/libmocoda.so\"
      AUTOCONF=${autoconf213}/bin/autoconf
      CXXFLAGS=\"-w -O0 -g0\"
      CCFLAGS=\"-w -O0 -g0\"

      mk_add_options AUTOCONF=${autoconf213}/bin/autoconf
      mk_add_options MOZ_MAKE_FLAGS="-j9"
      mk_add_options AUTOCLOBBER=1
      ac_add_options --disable-debug
      ac_add_options --disable-optimize
      ac_add_options --disable-debug-symbols
      "
    '';
  };

  mkBot = branch:
    let
      secretsKey = "repo:github.com/mozilla-releng/services:branch:" + branch;
      hook = mkTaskclusterHook {
        name = "Shipit task generating risk assessment data";
        owner = "cdenizet@mozilla.com";
        taskImage = self.docker;
        scopes = [
        ];
        taskEnv = {
          "SSL_CERT_FILE" = "${releng_pkgs.pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
          "APP_CHANNEL" = branch;
        };
        taskCommand = [
          "/bin/shipit-risk-assessment"
          "/work"
        ];
        deadline = "5 hours";
        maxRunTime = 18000;
      };
    in
      releng_pkgs.pkgs.writeText "taskcluster-hook-${self.name}.json" (builtins.toJSON hook);

  self = mkPython {
    inherit python name dirname version;
    src = filterSource ./. { inherit name; };
    buildInputs =
      fromRequirementsFile ./requirements-dev.txt python.packages;
    propagatedBuildInputs =
      fromRequirementsFile ./requirements.txt python.packages
      ++ [
        llvm_4
        sqlite
        libmocoda
        llvmPackages_4.clang-unwrapped
        gecko
      ];

    postInstall = ''
      mkdir -p $out/tmp
      mkdir -p $out/bin
      ln -s ${mercurial}/bin/hg $out/bin
      ln -s ${gecko}/bin/gecko-env $out/bin
    '';
    shellHook = ''
      export PATH="${mercurial}/bin:$PATH"
      export MOZCONFIG="${libmocoda}/conf/mozconfig"

      export EXTRAS_INCLUDE_PATH="${gcc-unwrapped}/include/c++/5.4.0:${gcc-unwrapped}/include/c++/5.4.0/backward:${gcc-unwrapped}/include/c++/5.4.0/x86_64-unknown-linux-gnu:${glibc.dev}/include/"
    '';
    dockerEnv =
      [ "MOZCONFIG=${libmocoda}/conf/mozconfig"
        "EXTRAS_INCLUDE_PATH=${gcc-unwrapped}/include/c++/5.4.0:${gcc-unwrapped}/include/c++/5.4.0/backward:${gcc-unwrapped}/include/c++/5.4.0/x86_64-unknown-linux-gnu:${glibc.dev}/include/"
      ];
    dockerCmd = [];

    passthru = {
      deploy = {
        staging = mkBot "staging";
        production = mkBot "production";
      };
      update = writeScript "update-${name}" ''
        pushd ${self.src_path}
        ${pypi2nix}/bin/pypi2nix -v \
          -V 3.5 \
          -E "libffi openssl pkgconfig freetype.dev" \
          -r requirements.txt \
          -r requirements-dev.txt
        popd
      '';
    };
  };

in self
