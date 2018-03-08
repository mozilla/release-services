{ releng_pkgs }:

let
  inherit (releng_pkgs.pkgs) fetchurl mercurial cacert ;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) licenses ;

  hg_tools = mkDerivation {
    name = "mozilla-hg-tools";
    src = fetchurl {
      url = "https://hg.mozilla.org/hgcustom/version-control-tools/archive/825b151d379c.tar.bz2";
      sha256 = "0l4i3x20irshf4xa2xy64nvqi04wrj2h92bn24v2j72nqmg6379x";
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

  mercurial_version = "4.4";

in mercurial.overrideDerivation (old: {
  name = "mercurial-${mercurial_version}";
  src = fetchurl {
    url = "https://mercurial-scm.org/release/mercurial-${mercurial_version}.tar.gz";
    sha256 = "1pl77mb7d1r0hwk571cvyq9cyjxl99q0r4d1n0imkj35fnkg8ji3";
  };
  postInstall = old.postInstall + ''
    mkdir -p $out/etc/mercurial
    cat > $out/etc/mercurial/hgrc <<EOF
    [web]
    cacerts = ${cacert}/etc/ssl/certs/ca-bundle.crt
    
    [extensions]
    purge =
    robustcheckout = ${hg_tools}/hgext/robustcheckout/__init__.py
    EOF
  '';
})
