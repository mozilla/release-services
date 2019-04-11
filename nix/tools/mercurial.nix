{ releng_pkgs }:

let
  inherit (releng_pkgs.pkgs) fetchurl mercurial cacert python2Packages makeWrapper docutils unzip;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) licenses;

  hg_tools = mkDerivation {
    name = "mozilla-hg-tools";
    src = fetchurl {
      url = "https://hg.mozilla.org/hgcustom/version-control-tools/archive/6cd994e30bb1.tar.bz2";
      sha256 = "0dh82jz7b1qqfv7ghrzf6xdgcgpk10z7338d90inyckk0naiac5g";
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

  # Stick to 4.8, which is supported by version-control-tools.
  version = "4.8";
  name = "mercurial-${version}";

in python2Packages.buildPythonApplication {
  inherit name;
  format = "other";

  src = fetchurl {
    url = "https://mercurial-scm.org/release/${name}.tar.gz";
    sha256 = "00rzjbf2blxkc0qwd9mdzx5fnzgpp4jxzijq6wgsjgmqscx40sy5";
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
