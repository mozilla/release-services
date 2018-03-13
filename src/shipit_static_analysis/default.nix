{ releng_pkgs 
}: 

let

  inherit (releng_pkgs.lib) mkTaskclusterHook mkTaskclusterMergeEnv mkPython fromRequirementsFile filterSource ;
  inherit (releng_pkgs.pkgs) writeScript gcc cacert gcc-unwrapped glibc glibcLocales xorg patch nodejs git python27 python35 coreutils shellcheck;
  inherit (releng_pkgs.pkgs.lib) fileContents concatStringsSep ;
  inherit (releng_pkgs.tools) pypi2nix mercurial;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  moz_clang = import ./mozilla_clang.nix { inherit releng_pkgs ; };
  name = "mozilla-shipit-static-analysis";
  dirname = "shipit_static_analysis";

  # Customize gecko environment with Nodejs & Python 3 for linters
  gecko-env = releng_pkgs.gecko-env.overrideDerivation(old : {
    buildPhase = old.buildPhase + ''
      echo "export PATH=${nodejs}/bin:${python35}/bin:\$PATH" >> $out/bin/gecko-env
    '';
 } );

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
        taskEnv = mkTaskclusterMergeEnv {
          env = {
            "SSL_CERT_FILE" = "${cacert}/etc/ssl/certs/ca-bundle.crt";
            "APP_CHANNEL" = branch;
            "MOZ_AUTOMATION" = "1";
          };
        };
        taskCommand = [
          "/bin/shipit-static-analysis"
          "--taskcluster-secret"
          secretsKey
          "--cache-root"
          "/cache"
        ];
        taskArtifacts = {
          "public/results" = {
            path = "/tmp/results";
            type = "directory";
          };
        };
      };
    in
      releng_pkgs.pkgs.writeText "taskcluster-hook-${self.name}.json" (builtins.toJSON hook);

  includes = concatStringsSep ":" [
    "${gcc-unwrapped}/include/c++/${gcc-unwrapped.version}"
    "${gcc-unwrapped}/include/c++/${gcc-unwrapped.version}/backward"
    "${gcc-unwrapped}/include/c++/${gcc-unwrapped.version}/x86_64-unknown-linux-gnu"
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
      [ mercurial ] ++ fromRequirementsFile ./requirements-dev.txt python.packages;
    propagatedBuildInputs =
      fromRequirementsFile ./requirements.txt python.packages
      ++ [
        # Needed for the static analysis
        glibc
        gcc
        moz_clang
        patch
        shellcheck

        # Needed for linters
        nodejs

        # Gecko environment
        gecko-env
      ];

    postInstall = ''
      mkdir -p $out/tmp
      mkdir -p $out/bin
      mkdir -p $out/usr/bin
      ln -s ${mercurial}/bin/hg $out/bin
      ln -s ${moz_clang}/bin/clang-tidy $out/bin
      ln -s ${moz_clang}/bin/clang-format $out/bin
      ln -s ${patch}/bin/patch $out/bin

      # Mozlint deps
      ln -s ${gcc}/bin/gcc $out/bin
      ln -s ${nodejs}/bin/node $out/bin
      ln -s ${nodejs}/bin/npm $out/bin
      ln -s ${git}/bin/git $out/bin
      ln -s ${python27}/bin/python2.7 $out/bin/python2.7
      ln -s ${python27}/bin/python2.7 $out/bin/python2
      ln -s ${python35}/bin/python3.5 $out/bin/python3.5
      ln -s ${python35}/bin/python3.5 $out/bin/python3
      ln -s ${coreutils}/bin/env $out/usr/bin/env
      ln -s ${coreutils}/bin/ld $out/bin
      ln -s ${coreutils}/bin/as $out/bin

      # Expose gecko env in final output
      ln -s ${gecko-env}/bin/gecko-env $out/bin
    '';

    shellHook = ''
      export PATH="${mercurial}/bin:${git}/bin:${python27}/bin:${python35}/bin:${moz_clang}/bin:${nodejs}/bin:$PATH"

      # Setup mach automation
      export MOZ_AUTOMATION=1

      # Use clang mozconfig from gecko-env
      export MOZCONFIG=${gecko-env}/conf/mozconfig

      # Extras for clang-tidy
      export CPLUS_INCLUDE_PATH=${includes}
      export C_INCLUDE_PATH=${includes}

      # Export linters tools
      export CODESPELL=${python.packages.codespell}/bin/codespell
      export SHELLCHECK=${shellcheck}/bin/shellcheck
    '';

    dockerEnv =
      [ "CPLUS_INCLUDE_PATH=${includes}"
        "C_INCLUDE_PATH=${includes}"
        "MOZCONFIG=${gecko-env}/conf/mozconfig"
        "CODESPELL=${python.packages.codespell}/bin/codespell"
        "SHELLCHECK=${shellcheck}/bin/shellcheck"
        "SHELL=xterm"
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
