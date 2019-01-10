{ releng_pkgs }:

let
  inherit (releng_pkgs.pkgs) fetchurl mercurial cacert python2Packages makeWrapper docutils unzip;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) licenses;

  hg_tools = mkDerivation {
    name = "mozilla-hg-tools";
    src = fetchurl {
      url = "https://hg.mozilla.org/hgcustom/version-control-tools/archive/f260c773c13f.tar.bz2";
      sha256 = "1llsqvl7mv02mfbjpn35s9hsqjd1414v81qc81kjwi3kzjbllfvn";
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

  buildInputs = [ makeWrapper docutils unzip ];

  makeFlags = [ "PREFIX=$(out)" ];

  postInstall = ''
    mkdir -p $out/etc/mercurial
    cat > $out/etc/mercurial/hgrc <<EOF
    [web]
    cacerts = ${cacert}/etc/ssl/certs/ca-bundle.crt
    
    [extensions]
    purge =
    robustcheckout = ${hg_tools}/hgext/robustcheckout/__init__.py
    hgmo = ${hg_tools}/hgext/hgmo
    pushlog = ${hg_tools}/hgext/pushlog
    EOF
  '';
}
