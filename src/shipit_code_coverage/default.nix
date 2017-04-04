{releng_pkgs }: 

let

  inherit (releng_pkgs.lib) mkPython fromRequirementsFile filterSource mkRustPlatform;
  inherit (releng_pkgs.pkgs) writeScript makeWrapper mercurial cacert rustStable ;
  inherit (releng_pkgs.pkgs.lib) fileContents optional licenses;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  rustPlatform = mkRustPlatform {};
  name = "mozilla-shipit-code-coverage";
  dirname = "shipit_code_coverage";

  mercurial' = mercurial.overrideDerivation (old: {
    postInstall = old.postInstall + ''
      cat > $out/etc/mercurial/hgrc <<EOF
[web]
cacerts = ${cacert}/etc/ssl/certs/ca-bundle.crt

[extensions]
purge =
EOF
    '';
  });

  # Marco grcov
  grcov = rustPlatform.buildRustPackage rec {
    version = "0.1.6";
    name = "grcov-${version}";

    src = releng_pkgs.pkgs.fetchFromGitHub {
      owner = "marco-c";
      repo = "grcov";
      rev = "v${version}";
      sha256 = "0smfza93h6xh673hrhx936zfx2kbz1ldmbn1nvm5isjwrqnvjf7k";
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

    depsSha256 = "1gyyxnisdd7a97i1xm8lg62hx1s8p5g92129xni7v14pwrivafvi";

    meta = with releng_pkgs.pkgs.stdenv.lib; {
      description = "grcov collects and aggregates code coverage information for multiple source files.";
      homepage = https://github.com/marco-c/grcov;
      license = with releng_pkgs.pkgs.lib.licenses; [ mit ];
      platforms = platforms.all;
    };
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
      mkdir -p $out/bin
      ln -s ${mercurial'}/bin/hg $out/bin
      ln -s ${releng_pkgs.pkgs.gcc}/bin/gcc $out/bin
      ln -s ${releng_pkgs.pkgs.lcov}/bin/lcov $out/bin
      ln -s ${rustStable.rustc}/bin/rustc $out/bin
      ln -s ${rustStable.cargo}/bin/cargo $out/bin
    '';
    passthru = {
      taskclusterHooks = {
        master = {
        };
        staging = {
        };
        production = {
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
