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

  "yarl" = python.overrideDerivation super."yarl" (old: {
    buildInputs = old.buildInputs ++ [ self."pytest-runner" ];
  });

  "mccabe" = python.overrideDerivation super."mccabe" (old: {
    buildInputs = old.buildInputs ++ [ self."pytest-runner" ];
  });

  "async-timeout" = python.overrideDerivation super."async-timeout" (old: {
    buildInputs = old.buildInputs ++ [ self."pytest-runner" ];
  });

  "clickclick" = python.overrideDerivation super."clickclick" (old: {
    buildInputs = old.buildInputs ++ [ self."flake8" self."six" ];
  });

  "pytest-runner" = python.overrideDerivation super."pytest-runner" (old: {
    buildInputs = old.buildInputs ++ [ self."setuptools-scm" ];
  });

}
