{ releng_pkgs
}:

let

  inherit (releng_pkgs.lib) mkPython2 fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript makeWrapper mercurial cacert ;
  inherit (releng_pkgs.pkgs.lib) fileContents optional licenses;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  project_name = "pulselistener";
  name = "mozilla-pulselistener";
  dirname = "pulselistener";

  mercurial' = mercurial.overrideDerivation (old: {
    postInstall = old.postInstall + ''
      mkdir -p $out/etc/mercurial
      cat > $out/etc/mercurial/hgrc <<EOF
      [web]
      cacerts = ${cacert}/etc/ssl/certs/ca-bundle.crt

      [extensions]
      purge =
      EOF
    '';
  });

  self = mkPython2 {
    inherit python project_name name dirname;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      (fromRequirementsFile ./../../lib/cli_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./requirements-dev.txt python.packages);
    propagatedBuildInputs =
      (fromRequirementsFile ./requirements.txt python.packages);
    postInstall = ''
      mkdir -p $out/bin
      ln -s ${mercurial'}/bin/hg $out/bin
    '';
    dockerCmd = [
      "/bin/pulselistener"
    ];
    passthru = {
      update = writeScript "update-${name}" ''
        pushd ${self.src_path}
        ${pypi2nix}/bin/pypi2nix -v \
          -V 3.6 \
          -E "libffi openssl pkgconfig freetype.dev" \
          -r requirements.txt \
          -r requirements-dev.txt
        popd
      '';
    };
  };

in self
