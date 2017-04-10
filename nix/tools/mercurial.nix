{ releng_pkgs }:

let
  inherit (releng_pkgs.pkgs) fetchurl mercurial cacert ;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) licenses ;

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

in mercurial.overrideDerivation (old: {
  postInstall = old.postInstall + ''
    cat > $out/etc/mercurial/hgrc <<EOF
[web]
cacerts = ${cacert}/etc/ssl/certs/ca-bundle.crt

[extensions]
purge =
robustcheckout = ${robustcheckout}/robustcheckout/__init__.py
EOF
  '';
})
