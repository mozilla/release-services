{ pkgs, python }:

self: super: {

  "pytest-runner" = python.overrideDerivation super."pytest-runner" (old: {
    buildInputs = old.buildInputs ++ [ self."setuptools-scm" ];
  });

  "async-timeout" = python.overrideDerivation super."async-timeout" (old: {
    buildInputs = old.buildInputs ++ [ self."pytest-runner" ];
  });

}
