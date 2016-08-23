{ pkgs, python }:

self: super: {

  "connexion" = python.overrideDerivation super."connexion" (old: {
    buildInputs = old.buildInputs ++ [ self."flake8" ];
    # TODO: report this upstream
    patchPhase = ''
      sed -i -e "s|long_description=open('README.rst').read(),|long_description=\"\",|" setup.py
      sed -i -e "s|base_url or self.base_url|\'\'|" connexion/api.py
    '';
  });

  "jsonschema" = python.overrideDerivation super."jsonschema" (old: {
    buildInputs = old.buildInputs ++ [ self."vcversioner" ];
  });

  "flake8" = python.overrideDerivation super."flake8" (old: {
    buildInputs = old.buildInputs ++ [ self."pytest-runner" ];
  });

  "mccabe" = python.overrideDerivation super."mccabe" (old: {
    buildInputs = old.buildInputs ++ [ self."pytest-runner" ];
  });


  "pytest-runner" = python.overrideDerivation super."pytest-runner" (old: {
    buildInputs = old.buildInputs ++ [ self."setuptools-scm" ];
  });

  "clouseau" = python.mkDerivation {
    name = "clouseau-0.1.1";
    src = pkgs.fetchFromGitHub
      { owner = "calixteman";
        repo = "clouseau";
        rev = "3b97b0d60b2e3ea4d68caa71b41c3b05c487bfaa";
        sha256 = "1nbkdiyyz8r8hi9l1ccnmr7lzy4m9h4lgags2k69j6jkd922z6hv";
      };
    patches = [
      (pkgs.fetchurl
        { url = "https://github.com/calixteman/clouseau/pull/68.patch";
          sha256 = "0f1j871yhcnjva6gk354v96rlkjnk01ylxlwwqyfyijd54rv3lgh";
        })
    ];
    postPatch = ''
     cat <<EOT >> MANIFEST.in
     recursive-include clouseau/*

     include VERSION
     include clouseau/*.json

     recursive-exclude * __pycache__
     recursive-exclude * *.py[co]
     EOT
    '';
    propagatedBuildInputs = [
      self."requests"
      self."requests-futures"
      self."six"
      self."whatthepatch"
      self."elasticsearch"
      self."python-dateutil"
      self."icalendar"
    ];
    doCheck = false;
  };

}
