{ releng_pkgs }: 

let

  inherit (builtins) readFile concatStringsSep;
  inherit (releng_pkgs.lib) fromRequirementsFile mkTaskclusterGithubTask;
  inherit (releng_pkgs.tools) pypi2nix;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) fileContents replaceStrings;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };

  name = "mozilla-releng-docs";
  version = fileContents ./../../VERSION;
  src_path =
    "src/" +
      (replaceStrings ["-"] ["_"]
        (builtins.substring 8
          (builtins.stringLength name - 8) name));

  self = mkDerivation {
    name = "${name}-${version}";
    src = ./.;

    buildInputs =
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
      cd ${src_path}
    '';

    passthru = {
      update  = writeScript "update-${name}" ''
        pushd ${src_path}
        ${pypi2nix}/bin/pypi2nix -v \
          -V 3.5 \
          -E "pkgconfig zlib libjpeg openjpeg libtiff freetype lcms2 libwebp tcl" \
          -r requirements.txt
        popd
      '';
    };

   };
in self
