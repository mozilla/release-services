{ releng_pkgs }: 

let

  inherit (builtins) readFile concatStringsSep;
  inherit (releng_pkgs.lib) fromRequirementsFile;
  inherit (releng_pkgs.pkgs.lib) removeSuffix;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;

  name = "releng_docs";

  version = removeSuffix "\n" (readFile ./../VERSION);

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };

  self = mkDerivation {
     name = "${name}-${version}";
     src = ./.;
     buildInputs = fromRequirementsFile [ ./requirements.txt ] python.packages;
     buildPhase = ''
       make html
     '';
     installPhase = ''
       mkdir -p $out
       cp -R build/html/* $out/
     '';
     passthru.updateSrc = releng_pkgs.pkgs.writeScriptBin "update" ''
       pushd src/${name}
       ${releng_pkgs.tools.pypi2nix}/bin/pypi2nix -v \
         -V 3.5 \
         -r requirements.txt
       popd
     '';
   };
in self
