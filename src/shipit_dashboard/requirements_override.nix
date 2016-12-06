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
		# Remove useless dependencies
    preConfigure = ''
      sed -i -e "s|mercurial>=3.9.1; python_version < '3.0'||" requirements.txt
      sed -i -e "s|setuptools>=28.6.1||" requirements.txt
    '';

		# Add temporary patches until next release
    patches = [
      # New uplift template
      (pkgs.fetchurl {
        url = "https://github.com/La0/libmozdata/commit/582e41af1c220ab680b2d72caef78be23394a18b.patch";
        sha256 = "04cwg30iwi5j2mdpbk67s0km0vlarac2fwyiqwx0cn5fa7ma9zvz";
      })

      # Language detection
      (pkgs.fetchurl {
        url = "https://github.com/La0/libmozdata/commit/a533aaad9b4580ad331563bed50cdc447ea664b9.patch";
        sha256 = "03vb8kis0gzyl7yss2za935vjcz1qfsx7l0qqjca3nynkggv5156";
      })
    ];
  });

}
