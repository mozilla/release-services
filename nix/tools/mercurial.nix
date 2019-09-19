{ releng_pkgs }:

let
  inherit (releng_pkgs.pkgs) fetchurl mercurial cacert python2Packages makeWrapper docutils unzip;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) licenses;

  hg_tools = mkDerivation {
    name = "mozilla-hg-tools";
    src = fetchurl {
      url = "https://hg.mozilla.org/hgcustom/version-control-tools/archive/307f3c28687630bf91b4c19c913f0c677e0ae724.tar.bz2";
      sha256 = "0m7s6vnmbyfps9gp7pspr5x6y8czj0adp8d5hq6n5gl18xrjhdhg";
    };
    installPhase = ''
      mkdir -p $out
      cp -rf * $out
    '';
    doCheck = false;
    buildInputs = [];
    propagatedBuildInputs = [ ];
    meta = {
      homepage = "https://hg.mozilla.org/hgcustom/version-control-tools";
      license = licenses.mit;
      description = "Mozilla Version Control Tools";
    };
  };

  # Stick to 5.1, which is supported by version-control-tools.
  version = "5.1";
  name = "mercurial-${version}";

in python2Packages.buildPythonApplication {
  inherit name;
  format = "other";

  src = fetchurl {
    url = "https://mercurial-scm.org/release/${name}.tar.gz";
    sha256 = "0af8wx5sn35l8c8sfj7cabx15i9b2di81ibx5d11wh8fhqnxj8k2";
  };

  buildInputs = [ makeWrapper python2Packages.docutils unzip ];

  makeFlags = [ "PREFIX=$(out)" ];

  postInstall = ''
    mkdir -p $out/etc/mercurial
    cat > $out/etc/mercurial/hgrc <<EOF
    [web]
    cacerts = ${cacert}/etc/ssl/certs/ca-bundle.crt
    
    [extensions]
    purge =
    strip =
    robustcheckout = ${hg_tools}/hgext/robustcheckout/__init__.py
    hgmo = ${hg_tools}/hgext/hgmo
    pushlog = ${hg_tools}/hgext/pushlog
    mozext = ${hg_tools}/hgext/mozext
    firefoxtree = ${hg_tools}/hgext/firefoxtree
    EOF
  '';
}
