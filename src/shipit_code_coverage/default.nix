{releng_pkgs }: 

let

  inherit (releng_pkgs.lib) mkTaskclusterHook mkTaskclusterMergeEnv mkPython fromRequirementsFile filterSource mkRustPlatform;
  inherit (releng_pkgs.pkgs) writeScript makeWrapper fetchurl cacert git llvm_4;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) fileContents optional licenses;
  inherit (releng_pkgs.tools) pypi2nix mercurial ;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  rustPlatform = mkRustPlatform {};
  name = "mozilla-shipit-code-coverage";
  dirname = "shipit_code_coverage";

  # Marco grcov
  grcov = rustPlatform.buildRustPackage rec {
    version = "0.1.33";
    name = "grcov-${version}";

    buildInputs = [
        llvm_4
    ];

    src = releng_pkgs.pkgs.fetchFromGitHub {
      owner = "marco-c";
      repo = "grcov";
      rev = "v${version}";
      sha256 = "00lyyrb4w4r2hfgii89w5r1cs86kx5p9xvw5rqcfm9gjjp04nvhy";
    };

	# ...
    # failures:
    #     test_integration
    # test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out
    # error: test failed, to rerun pass '--test test'
    doCheck = false;

    cargoSha256 = "0wqsg8cg403vc6f7gikf0rzm9ywbp29fxpmb4kaa1pybq9v9v00s";

    meta = with releng_pkgs.pkgs.stdenv.lib; {
      description = "grcov collects and aggregates code coverage information for multiple source files.";
      homepage = https://github.com/marco-c/grcov;
      license = with releng_pkgs.pkgs.lib.licenses; [ mit ];
      platforms = platforms.all;
    };
  };

  mkBot = branch:
    let
      cacheKey = "services-" + branch + "-shipit-code-coverage";
      secretsKey = "repo:github.com/mozilla-releng/services:branch:" + branch;
      hook = mkTaskclusterHook {
        name = "Shipit task aggregating code coverage data";
        owner = "mcastelluccio@mozilla.com";
        schedule = [ "0 0 0 * * 0" ]; # every week
        taskImage = self.docker;
        scopes = [
          # Used by taskclusterProxy
          ("secrets:get:" + secretsKey)

          # Needed to notify about patches with low coverage
          ("notify:email:*")

          # Used by cache
          ("docker-worker:cache:" + cacheKey)

          # Needed to post build status to GitHub
          ("github:create-status:marco-c/gecko-dev")
        ];
        cache = {
          "${cacheKey}" = "/cache";
        };
        taskEnv = mkTaskclusterMergeEnv {
          env = {
            "SSL_CERT_FILE" = "${releng_pkgs.pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
            "APP_CHANNEL" = branch;
          };
        };
        taskCommand = [
          "/bin/shipit-code-coverage"
          "--taskcluster-secret"
          secretsKey
          "--cache-root"
          "/cache"
        ];
        deadline = "4 hours";
        maxRunTime = 4 * 60 * 60;
        workerType = "releng-svc-compute";
      };
    in
      releng_pkgs.pkgs.writeText "taskcluster-hook-${self.name}.json" (builtins.toJSON hook);

  self = mkPython {
    inherit python name dirname;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      fromRequirementsFile ./requirements-dev.txt python.packages;
    propagatedBuildInputs =
      fromRequirementsFile ./requirements.txt python.packages 
      ++ [
        releng_pkgs.pkgs.gcc
        releng_pkgs.pkgs.lcov
        rustPlatform.rust.rustc
        rustPlatform.rust.cargo
        grcov
      ];
    postInstall = ''
      mkdir -p $out/tmp
      mkdir -p $out/bin
      ln -s ${mercurial}/bin/hg $out/bin

      # Needed by grcov runtime
      ln -s ${releng_pkgs.pkgs.gcc}/bin/gcc $out/bin
      ln -s ${releng_pkgs.pkgs.gcc.cc}/bin/gcov $out/bin
      ln -s ${releng_pkgs.pkgs.lcov}/bin/lcov $out/bin
      ln -s ${releng_pkgs.pkgs.lcov}/bin/genhtml $out/bin
      ln -s ${rustPlatform.rust.rustc}/bin/rustc $out/bin
      ln -s ${rustPlatform.rust.cargo}/bin/cargo $out/bin
    '';
    shellHook = ''
      export PATH="${mercurial}/bin:$PATH"
    '';
    dockerContents = [ git ];
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
