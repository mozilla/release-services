{ releng_pkgs 
}: 

let

  inherit (releng_pkgs.lib) mkTaskclusterHook mkPython fromRequirementsFile filterSource ;
  inherit (releng_pkgs.pkgs) writeScript makeWrapper fetchurl dockerTools gcc
      cacert gcc-unwrapped glibc glibcLocales xorg llvmPackages_4;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) fileContents optional licenses concatStringsSep ;
  inherit (releng_pkgs.tools) pypi2nix mercurial;
  inherit (releng_pkgs.pkgs.pythonPackages) setuptools;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  name = "mozilla-shipit-static-analysis";
  dirname = "shipit_static_analysis";

  clang = llvmPackages_4.clang-unwrapped;

  moz_clang = clang.overrideDerivation (old: {
    # Add mozilla clang-plugin source for clang-tidy
    plugin = filterSource ./clang-plugin { inherit name; };
    unpackPhase = old.unpackPhase + ''
      dest=$sourceRoot/tools/extra/clang-tidy/mozilla
      mkdir $dest
      cp -rf $plugin/* $dest
    '';

    # Patch Cmake files, as is described in
    # https://dxr.mozilla.org/mozilla-central/source/build/clang-plugin/import_mozilla_checks.py
    postPatch = old.postPatch + ''

      # TODO: generate CMakeLists.txt with list of cpp (write_cmake)
      # TODO: generate ThirdPartyPaths.cpp & restore in local CMakeLists.txt

      # Add clangTidyMozillaModule to LINK_LIBS
      target=$sourceRoot/tools/extra/clang-tidy/plugin/CMakeLists.txt
      sed '/LINK_LIBS/a \ \ clangTidyMozillaModule' -i $target

      # Add clangTidyMozillaModule to target_link_libraries
      target=$sourceRoot/tools/extra/clang-tidy/tool/CMakeLists.txt
      sed '/target_link_libraries(clang-tidy/a \ \ clangTidyMozillaModule' -i $target

      # Activate plugin
      target=$sourceRoot/tools/extra/clang-tidy/CMakeLists.txt
      echo 'add_subdirectory(mozilla)' >> $target

      # Add inline patch
      target=$sourceRoot/tools/extra/clang-tidy/tool/ClangTidyMain.cpp
      echo '// This anchor is used to force the linker to link the MozillaModule.' >> $target
      echo 'extern volatile int MozillaModuleAnchorSource;' >> $target
      echo 'static int LLVM_ATTRIBUTE_UNUSED MozillaModuleAnchorDestination = MozillaModuleAnchorSource;' >> $target
    '';

  });

  mkBot = branch:
    let
      cacheKey = "services-" + branch + "-shipit-static-analysis";
      secretsKey = "repo:github.com/mozilla-releng/services:branch:" + branch;
      hook = mkTaskclusterHook {
        name = "Static analysis automated tests";
        owner = "jan@mozilla.com";
        taskImage = self.docker;
        scopes = [
          # Used by taskclusterProxy
          ("secrets:get:" + secretsKey)

          # Send emails to relman
          "notify:email:*"

          # Used by cache
          ("docker-worker:cache:" + cacheKey)
        ];
        cache = {
          "${cacheKey}" = "/cache";
        };
        taskEnv = {
          "SSL_CERT_FILE" = "${releng_pkgs.pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
          "APP_CHANNEL" = branch;
          "MOZ_AUTOMATION" = "1";
        };
        taskCommand = [
          "/bin/shipit-static-analysis"
          "--taskcluster-secret"
          secretsKey
          "--cache-root"
          "/cache"
        ];
      };
    in
      releng_pkgs.pkgs.writeText "taskcluster-hook-${self.name}.json" (builtins.toJSON hook);

  includes = concatStringsSep ":" [
    "${gcc-unwrapped}/include/c++/5.4.0"
    "${gcc-unwrapped}/include/c++/5.4.0/backward"
    "${gcc-unwrapped}/include/c++/5.4.0/x86_64-unknown-linux-gnu"
    "${glibc.dev}/include/"
    "${xorg.libX11.dev}/include"
    "${xorg.xproto}/include"
    "${xorg.libXrender.dev}/include"
    "${xorg.renderproto}/include"
  ];

  self = mkPython {
    inherit python name dirname;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      fromRequirementsFile ./requirements-dev.txt python.packages;
    propagatedBuildInputs =
      fromRequirementsFile ./requirements.txt python.packages
      ++ [
        # Needed for the static analysis
				glibc
				gcc

        # Gecko environment
        releng_pkgs.gecko-env
      ];

    postInstall = ''
      mkdir -p $out/tmp
      mkdir -p $out/bin
      ln -s ${mercurial}/bin/hg $out/bin
      ln -s ${moz_clang}/bin/clang-tidy $out/bin

      # Expose gecko env in final output
      ln -s ${releng_pkgs.gecko-env}/bin/gecko-env $out/bin
    '';

    shellHook = ''
      export PATH="${mercurial}/bin:${moz_clang}/bin:$PATH"

      # Setup mach automation
      export MOZ_AUTOMATION=1

      # Use clang mozconfig from gecko-env
      export MOZCONFIG=${releng_pkgs.gecko-env}/conf/mozconfig

      # Extras for clang-tidy
      export CPLUS_INCLUDE_PATH=${includes}
      export C_INCLUDE_PATH=${includes}
    '';

    dockerEnv =
      [ "CPLUS_INCLUDE_PATH=${includes}"
        "C_INCLUDE_PATH=${includes}"
        "MOZCONFIG=${releng_pkgs.gecko-env}/conf/mozconfig"
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
