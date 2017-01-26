{ pkgs, python }:

self: super: {

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

  "pytest-runner" = python.overrideDerivation super."pytest-runner" (old: {
    buildInputs = old.buildInputs ++ [ self."setuptools-scm" ];
  });

  "taskcluster" = python.overrideDerivation super."taskcluster" (old: {
    patches = [ (pkgs.fetchurl { url = "https://github.com/La0/taskcluster-client.py/commit/042cda02e70fca879ad47509f1bde0ed471ab6bd.diff"; sha256 = "0aqgqy5mvydl3yj6ply5f6c16fh3cvql900jxaran8ya1vzsnkz8"; }) ];
  });

  "libmozdata" = python.overrideDerivation super."libmozdata" (old: {
		# Remove useless dependencies
    preConfigure = ''
      sed -i -e "s|mercurial>=3.9.1; python_version < '3.0'||" requirements.txt
      sed -i -e "s|setuptools>=28.6.1||" requirements.txt
    '';
  });

}
