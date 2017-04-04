{ releng_pkgs 
}: 

let

  inherit (releng_pkgs.lib) mkPython fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript makeWrapper fetchurl ;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) fileContents optional licenses;
  inherit (releng_pkgs.tools) pypi2nix;

  inherit (releng_pkgs.pkgs) rustStable cacert fetchFromGitHub pythonFull which autoconf213
    perl unzip zip gnumake yasm pkgconfig xlibs gnome2 pango dbus dbus_glib
    alsaLib libpulseaudio gstreamer gst_plugins_base gtk3 glib
    gobjectIntrospection git mercurial openssl cmake
    clang clang-tools;

  inherit (releng_pkgs.pkgs.pythonPackages) setuptools;

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
      ]
      ++ [
        # TODO: Use nixpkgs-mozilla gecko buildInputs
        # From https://github.com/mozilla/nixpkgs-mozilla/blob/master/pkgs/gecko/default.nix
        # Expected by "mach"
        setuptools which autoconf213

        # Expected by the configure script
        perl unzip zip gnumake yasm pkgconfig

        xlibs.libICE xlibs.libSM xlibs.libX11 xlibs.libXau xlibs.libxcb
        xlibs.libXdmcp xlibs.libXext xlibs.libXt xlibs.printproto
        xlibs.renderproto xlibs.xextproto xlibs.xproto xlibs.libXcomposite
        xlibs.compositeproto xlibs.libXfixes xlibs.fixesproto
        xlibs.damageproto xlibs.libXdamage xlibs.libXrender xlibs.kbproto

        gnome2.libart_lgpl gnome2.libbonobo gnome2.libbonoboui
        gnome2.libgnome gnome2.libgnomecanvas gnome2.libgnomeui
        gnome2.libIDL

        pango

        dbus dbus_glib

        alsaLib libpulseaudio
        gstreamer gst_plugins_base

        gtk3 glib gobjectIntrospection

        rustStable.rustc rustStable.cargo

        # "mach vendor rust" wants to list modified files by using the vcs.
        # mercurial is already there !
        git 

        # needed for compiling cargo-vendor and its dependencies
        openssl cmake
      ];

    postInstall = ''
      mkdir -p $out/bin
      ln -s ${mercurial'}/bin/hg $out/bin
      ln -s ${rustStable.rustc}/bin/rustc $out/bin
      ln -s ${rustStable.cargo}/bin/cargo $out/bin
    '';
		shellHook = ''
			export PATH="${mercurial'}/bin:$PATH"
			#export PKG_CONFIG_PATH="${releng_pkgs.pkgs.gtk3}/bin:$PKG_CONFIG_PATH"
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
