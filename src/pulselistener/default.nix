{ releng_pkgs
}:

let

  inherit (releng_pkgs.lib) mkPython fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript makeWrapper mercurial cacert ;
  inherit (releng_pkgs.pkgs.lib) fileContents optional licenses;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  project_name = "pulselistener";

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

  self = mkPython {
    inherit python project_name;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit (self) name; };
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
      update = writeScript "update-${self.name}" ''
        pushd ${self.src_path}
        cache_dir=$PWD/../../../tmp/pypi2nix
        mkdir -p $cache_dir
        eval ${pypi2nix}/bin/pypi2nix -v \
          -C $cache_dir \
          -V 3.7 \
          -O ../../nix/requirements_override.nix \
          -E libffi \
          -E openssl \
          -E pkgconfig \
          -E freetype.dev \
          -s intreehooks \
          -s flit \
          -s pytest-runner \
          -s setuptools-scm \
          -r requirements.txt \
          -r requirements-dev.txt
        popd
      '';
    };
  };

in self
