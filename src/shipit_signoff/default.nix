{ releng_pkgs
}: 

let

  inherit (releng_pkgs.lib) mkBackend fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript glibcLocales;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  name = "mozilla-shipit-signoff";
  dirname = "shipit_signoff";

  self = mkBackend {
    inherit python name dirname;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit name; };
    checkPhase = ''
      export LANG=en_US.UTF-8
      export LOCALE_ARCHIVE=${glibcLocales}/lib/locale/locale-archive
      export APP_TESTING=${name}

      flake8 --exclude=nix_run_setup.py,migrations/,build/
      #TODO: need to make tests work
      #pytest tests/
    '';
    buildInputs =
      fromRequirementsFile ./requirements-dev.txt python.packages;
    propagatedBuildInputs =
      fromRequirementsFile ./requirements.txt python.packages;
    passthru = {
      update = writeScript "update-${name}" ''
        pushd ${self.src_path}
        ${pypi2nix}/bin/pypi2nix -v \
          -V 3.5 \
          -E "postgresql" \
          -r requirements.txt \
          -r requirements-dev.txt
        sed -i -e "/^mozilla-/ d" requirements_frozen.txt
        popd
      '';
    };
  };

in self
