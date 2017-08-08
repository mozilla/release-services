{ releng_pkgs 
}: 

let

  inherit (releng_pkgs.lib) mkTaskclusterHook mkPython fromRequirementsFile filterSource ;
  inherit (releng_pkgs.pkgs) writeScript makeWrapper fetchurl dockerTools gcc
      cacert gcc-unwrapped glibc glibcLocales xorg;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) fileContents optional licenses concatStringsSep ;
  inherit (releng_pkgs.tools) pypi2nix mercurial;
  inherit (releng_pkgs.pkgs.pythonPackages) setuptools;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  name = "mozilla-shipit-static-analysis";
  dirname = "shipit_static_analysis";

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

      # Expose gecko env in final output
      ln -s ${releng_pkgs.gecko-env}/bin/gecko-env $out/bin
    '';

    shellHook = ''
      export PATH="${mercurial}/bin:$PATH"

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
