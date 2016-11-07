{ pkgs, python }:

self: super: {

  "async-timeout" = python.overrideDerivation super."async-timeout" (old: {
    buildInputs = old.buildInputs ++ [ self."pytest-runner" ];
  });

  "clickclick" = python.overrideDerivation super."clickclick" (old: {
    buildInputs = old.buildInputs ++ [ self."flake8" self."six" ];
  });

  "connexion" = python.overrideDerivation super."connexion" (old: {
    buildInputs = old.buildInputs ++ [ self."flake8" ];
  });

  "flake8" = python.overrideDerivation super."flake8" (old: {
    buildInputs = old.buildInputs ++ [ self."pytest-runner" ];
  });

  "jsonschema" = python.overrideDerivation super."jsonschema" (old: {
    buildInputs = old.buildInputs ++ [ self."vcversioner" ];
  });

  "mccabe" = python.overrideDerivation super."mccabe" (old: {
    buildInputs = old.buildInputs ++ [ self."pytest-runner" ];
  });

  "pytest-runner" = python.overrideDerivation super."pytest-runner" (old: {
    buildInputs = old.buildInputs ++ [ self."setuptools-scm" ];
  });

}
