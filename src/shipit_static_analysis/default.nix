{ releng_pkgs 
}: 

let

  inherit (releng_pkgs.lib) mkPython fromRequirementsFile filterSource ;
  inherit (releng_pkgs.pkgs.lib.customisation) addPassthru;
  inherit (releng_pkgs.pkgs) writeScript makeWrapper fetchurl dockerTools
      mercurial cacert clang llvmPackages_39 clang-tools rustStable;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) fileContents optional licenses ;
  inherit (releng_pkgs.tools) pypi2nix;
  inherit (releng_pkgs.pkgs.pythonPackages) setuptools;
  inherit (releng_pkgs.mozilla) gecko;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  name = "mozilla-shipit-static-analysis";
  dirname = "shipit_static_analysis";

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

  geckoCustom = gecko.overrideDerivation (old: {
    # Dummy src, cannot be null
    src = ./.;
    configurePhase = ''
      mkdir -p $out/bin

      # Gecko build environment
      geckoenv=$out/bin/gecko-env.sh
      echo "# Gecko dev env" > $geckoenv
      echo "SHELL=xterm" >> $geckoenv
      env | grep -e '^PATH=' >> $geckoenv
      env | grep -e '^PKG_CONFIG_PATH=' >> $geckoenv
      env | grep -e '^CMAKE_INCLUDE_PATH=' >> $geckoenv
      echo "CPLUS_INCLUDE_PATH=$CMAKE_INCLUDE_PATH" >> $geckoenv
      echo "C_INCLUDE_PATH=$CMAKE_INCLUDE_PATH" >> $geckoenv

      # Transform LDFLAGS in list of paths for LIBRARY_PATH
      ldflags=$(env | grep -e '^NIX_LDFLAGS=' | cut -c13-)
      echo "LIBRARY_PATH=$(echo $ldflags | sed -E 's,-rpath ([/\.a-zA-Z0-9\-]+) ,,g' | sed -e 's, -L,:,g')" >> $geckoenv
      chmod +x $geckoenv
    '';
    buildPhase = ''
      echo "Skip build"
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
  });

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
        # Needed for the static analysis
        clang
        clang-tools
      ];

    postInstall = ''
      mkdir -p $out/tmp
      mkdir -p $out/bin
      ln -s ${mercurial'}/bin/hg $out/bin
      ln -s ${clang-tools}/bin/clang-tidy $out/bin
      ln -s ${llvmPackages_39.clang-unwrapped}/share/clang/run-clang-tidy.py $out/bin
    '';

		shellHook = ''
			export PATH="${mercurial'}/bin:$PATH"
		'';

    # Our patched Gecko is embedded in the docker image
    dockerContents = [geckoCustom];

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
