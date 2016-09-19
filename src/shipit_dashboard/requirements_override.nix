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

  "taskcluster" = python.overrideDerivation super."taskcluster" (old: {
    patches = [ (pkgs.fetchurl { url = "https://github.com/taskcluster/taskcluster-client.py/pull/56.patch"; sha256 = "0g5z4gkkkz58p1gcq5ym9aw9rgcmidgs64mil22sxr9y7iq6mj4m"; }) ];
  });

}
