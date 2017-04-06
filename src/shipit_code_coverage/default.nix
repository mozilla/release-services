{releng_pkgs }: 

let

  inherit (releng_pkgs.lib) mkTaskclusterHook mkPython fromRequirementsFile filterSource mkRustPlatform;
  inherit (releng_pkgs.pkgs) writeScript makeWrapper fetchurl mercurial cacert rustStable ;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) fileContents optional licenses;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  rustPlatform = mkRustPlatform {};
  name = "mozilla-shipit-code-coverage";
  dirname = "shipit_code_coverage";

  robustcheckout = mkDerivation {
    name = "robustcheckout";
    src = fetchurl {
      url = "https://hg.mozilla.org/hgcustom/version-control-tools/archive/1a8415be17e8.tar.bz2";
      sha256 = "005n7ar8cn7162s1qx970x1aabv263zp7mxm38byxc23nzym37kn";
    };
    installPhase = ''
      mkdir -p $out
      cp -rf hgext/robustcheckout $out
    '';
    doCheck = false;
    buildInputs = [];
    propagatedBuildInputs = [ ];
    meta = {
      homepage = "https://hg.mozilla.org/hgcustom/version-control-tools";
      license = licenses.mit;
      description = "Mozilla Version Control Tools: robustcheckout";
    };
  };

  mercurial' = mercurial.overrideDerivation (old: {
    postInstall = old.postInstall + ''
      cat > $out/etc/mercurial/hgrc <<EOF
[web]
cacerts = ${cacert}/etc/ssl/certs/ca-bundle.crt

[extensions]
purge =
robustcheckout = ${robustcheckout}/robustcheckout/__init__.py
EOF
    '';
  });

  # Marco grcov
  grcov = rustPlatform.buildRustPackage rec {
    version = "0.1.8";
    name = "grcov-${version}";

    src = releng_pkgs.pkgs.fetchFromGitHub {
      owner = "marco-c";
      repo = "grcov";
      rev = "v${version}";
      sha256 = "06gd0h3ba2nwkdxb2zhq4r3kf1axygh5ia3d917d2lj44fyizjvq";
    };

    # running 4 tests
    # test test_merge_results ... ok
    # test test_producer ... FAILED
    # test test_zip_producer ... ok
    # test test_parser ... ok
    #
    # failures:
    #
    # ---- test_producer stdout ----
    #     thread 'test_producer' panicked at 'Missing grcov/test/Platform.gcda', src/main.rs:97
    # note: Run with `RUST_BACKTRACE=1` for a backtrace.
    #
    #
    # failures:
    #     test_producer
    #
    # test result: FAILED. 3 passed; 1 failed; 0 ignored; 0 measured
    #
    # error: test failed
    doCheck = false;

    depsSha256 = "0w8a09bijrqkfb6a6wyp67bwrhh7bm3pw0s2gx9aipbgc113q4ll";

    meta = with releng_pkgs.pkgs.stdenv.lib; {
      description = "grcov collects and aggregates code coverage information for multiple source files.";
      homepage = https://github.com/marco-c/grcov;
      license = with releng_pkgs.pkgs.lib.licenses; [ mit ];
      platforms = platforms.all;
    };
  };

  mkBot = branch:
    let
      secretsKey = "repo:github.com/mozilla-releng/services:branch:" + branch;
    in
      mkTaskclusterHook {
        name = "Shipit task aggregating code coverage data";
        owner = "mcastelluccio@mozilla.com";
        schedule = [ "0 0 0 * * *" ];  # every day
        taskImage = self.docker;
        scopes = [
          # Used by taskclusterProxy
          ("secrets:get:" + secretsKey)
        ];
        taskEnv = {
          "SSL_CERT_FILE" = "${releng_pkgs.pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
        };
        taskCommand = [
          "/bin/shipit-code-coverage"
          "--secrets"
          secretsKey
        ];
        deadline = "5 hours";
        maxRunTime = 18000;
      };

  self = mkPython {
    inherit python name dirname;
    inProduction = true;
    version = fileContents ./../../VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      fromRequirementsFile ./requirements-dev.txt python.packages;
    propagatedBuildInputs =
      fromRequirementsFile ./requirements.txt python.packages 
      ++ [
        releng_pkgs.pkgs.gcc
        releng_pkgs.pkgs.lcov
        rustStable.rustc
        rustStable.cargo
        grcov
      ];
    postInstall = ''
      mkdir -p $out/tmp
      mkdir -p $out/bin
      ln -s ${mercurial'}/bin/hg $out/bin

      # Needed by grcov runtime
      ln -s ${releng_pkgs.pkgs.gcc}/bin/gcc $out/bin
      ln -s ${releng_pkgs.pkgs.gcc.cc}/bin/gcov $out/bin
      ln -s ${releng_pkgs.pkgs.lcov}/bin/lcov $out/bin
      ln -s ${rustStable.rustc}/bin/rustc $out/bin
      ln -s ${rustStable.cargo}/bin/cargo $out/bin
    '';
    shellHook = ''
      export PATH="${mercurial'}/bin:$PATH"
    '';
    passthru = {
      taskclusterHooks = {
        master = {
        };
        staging = {
          bot = mkBot "staging";
        };
        production = {
          bot = mkBot "production";
        };
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
