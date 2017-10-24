{ releng_pkgs }:

let
  inherit (releng_pkgs.pkgs) fetchurl mercurial cacert ;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) licenses ;

  hg_tools = mkDerivation {
    name = "mozilla-hg-tools";
    src = fetchurl {
      url = "https://hg.mozilla.org/hgcustom/version-control-tools/archive/e05bed1064ed.tar.bz2";
      sha256 = "1icg8cvjpw5x0xapryhmjqsmm2amzh57pnqd7r0idf6h8mphpimp";
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


in mercurial.overrideDerivation (old: {
  postInstall = old.postInstall + ''
    cat > $out/etc/mercurial/hgrc <<EOF
[web]
cacerts = ${cacert}/etc/ssl/certs/ca-bundle.crt

[extensions]
purge =
robustcheckout = ${hg_tools}/hgext/robustcheckout/__init__.py
reviewboard = ${hg_tools}/hgext/reviewboard/client.py
EOF
  '';
})
