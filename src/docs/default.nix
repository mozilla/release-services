{ releng_pkgs }:

let

  inherit (builtins) readFile concatStringsSep;
  inherit (releng_pkgs.lib) fromRequirementsFile mkProject mkProjectFullName;
  inherit (releng_pkgs.tools) pypi2nix;
  inherit (releng_pkgs.pkgs) writeScript graphviz-nox;
  inherit (releng_pkgs.pkgs.lib) fileContents replaceStrings;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };

  project_name = "docs";
  version = fileContents ./VERSION;

  self = mkProject {
    inherit project_name version;

    src = ./.;

    buildInputs =
      [ graphviz-nox ] ++
      fromRequirementsFile ./requirements.txt python.packages;

    buildPhase = ''
      make html RELENG_DOCS_VERSION=${version}
    '';

    installPhase = ''
      mkdir -p $out
      cp -R build/html/* $out/
    '';

    shellHook = ''
      export RELENG_DOCS_VERSION=${version}-dev
      cd ${self.src_path}
    '';

    passthru = {
      deploy = {
        testing = self;
        staging = self;
        production = self;
      };
      update  = writeScript "update-${self.name}" ''
        pushd ${self.src_path}
        cache_dir=$PWD/../../../tmp/pypi2nix
        mkdir -p $cache_dir
        eval ${pypi2nix}/bin/pypi2nix -v \
          -C $cache_dir \
          -V 3.7 \
          -O ../../nix/requirements_override.nix \
          -E pkgconfig \
          -E zlib \
          -E libjpeg \
          -E openjpeg \
          -E libtiff \
          -E freetype \
          -E lcms2 \
          -E libwebp \
          -E tcl \
          -r requirements.txt
        popd
      '';
    };

   };
in self
