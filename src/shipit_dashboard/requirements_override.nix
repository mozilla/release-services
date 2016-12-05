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

  "taskcluster" = python.overrideDerivation super."taskcluster" (old: {
    patches = [ (pkgs.fetchurl { url = "https://github.com/taskcluster/taskcluster-client.py/pull/56.patch"; sha256 = "1k29primpv3fa62b1wq52shwvjamcja1m6ph66vykxab5ywmfkfw"; }) ];
  });

  "libmozdata" = python.overrideDerivation super."libmozdata" (old: {
		# Remove useless depencies
    preConfigure = ''
      sed -i -e "s|mercurial>=3.9.1; python_version < '3.0'||" requirements.txt
      sed -i -e "s|setuptools>=28.6.1||" requirements.txt
    '';
  });

}
