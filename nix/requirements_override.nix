{ pkgs, python }:

let

  inherit (pkgs.lib) fileContents;

  skipOverrides = overrides: self: super:
    let
      overridesNames = builtins.attrNames overrides;
      superNames = builtins.attrNames super;
    in
      builtins.listToAttrs
        (builtins.map
          (name: { inherit name;
                   value = python.overrideDerivation super."${name}" (overrides."${name}" self);
                 }
          )
          (builtins.filter
            (name: builtins.elem name superNames)
            overridesNames
          )
        );

  cli_common_path =
    if builtins.pathExists ./../lib/cli_common
    then ./../lib/cli_common/default.nix
    else ./../../lib/cli_common/default.nix;

  backend_common_path =
    if builtins.pathExists ./../lib/backend_common
    then ./../lib/backend_common/default.nix
    else ./../../lib/backend_common/default.nix;

in skipOverrides {

  # enable test for common packages

  "mozilla-cli-common" = import cli_common_path { inherit pkgs; };
  "mozilla-backend-common" = import backend_common_path { inherit pkgs; };

  # -- in alphabetic order --

  "RBTools" = self: old: {
    patches = [
         (pkgs.fetchurl {
           url = "https://github.com/La0/rbtools/commit/60a96a29c26fd1a546bb66a5860e2b6b36649d58.diff";
           sha256 = "1q0gpknxymm3qg4mb1459ka4ralqa1bndyfv3g3pn4sj7rixv05f";
         })
      ];
  };

  "cryptography" = self: old: {
    propagatedBuildInputs =
      builtins.filter
        (x: ! (pkgs.lib.hasSuffix "-flake8" (builtins.parseDrvName x.name).name))
        old.propagatedBuildInputs;
  };

  "en-core-web-sm" = self: old: {
    propagatedBuildInputs =
      builtins.filter
        (x: ! (pkgs.lib.hasSuffix "-spacy" (builtins.parseDrvName x.name).name))
        old.propagatedBuildInputs;
    patchPhase = ''
      sed -i -e "s|return requirements|return []|" setup.py
    '';
  };

  "numpy" = self: old: {
    preConfigure = ''
      sed -i 's/-faltivec//' numpy/distutils/system_info.py
    '';
    preBuild = ''
      echo "Creating site.cfg file..."
      cat << EOF > site.cfg
      [openblas]
      include_dirs = ${pkgs.openblasCompat}/include
      library_dirs = ${pkgs.openblasCompat}/lib
      EOF
    '';
    passthru = {
      blas = pkgs.openblasCompat;
    };
  };

  "pluggy" = self: old: {
    buildInputs = old.buildInputs ++ [ self."setuptools-scm" ];
  };

  "pytest" = self: old: {
    buildInputs = old.buildInputs ++ [ self."setuptools-scm" ];
  };

  "scipy" = self: old: {
    prePatch = ''
      rm scipy/linalg/tests/test_lapack.py
    '';
    preConfigure = ''
      sed -i '0,/from numpy.distutils.core/s//import setuptools;from numpy.distutils.core/' setup.py
    '';
    preBuild = ''
      echo "Creating site.cfg file..."
      cat << EOF > site.cfg
      [openblas]
      include_dirs = ${pkgs.openblasCompat}/include
      library_dirs = ${pkgs.openblasCompat}/lib
      EOF
    '';
    setupPyBuildFlags = [ "--fcompiler='gnu95'" ];
    passthru = {
      blas = pkgs.openblasCompat;
    };
  };

  "taskcluster-urls" = self: old: {
    patchPhase = ''
      # until this is fixed https://github.com/taskcluster/taskcluster-proxy/pull/37
      sed -i -e "s|/api/|/|" taskcluster_urls/__init__.py
    '';
  };
}
