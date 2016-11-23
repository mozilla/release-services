{ releng_pkgs }: 

let

  inherit (builtins) readFile concatStringsSep;
  inherit (releng_pkgs.lib) fromRequirementsFile mkTaskclusterGithubTask;
  inherit (releng_pkgs.tools) pypi2nix;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) removeSuffix;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;

  name = "releng_docs";
  version = removeSuffix "\n" (readFile ./../../VERSION);
  src_path = "src/${name}";

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };

  self = mkDerivation {
    name = "${name}-${version}";
    src = ./.;

    buildInputs = fromRequirementsFile [ ./requirements.txt ] python.packages;

    buildPhase = ''
      make html RELENG_DOCS_VERSION=${version}
    '';

    installPhase = ''
      mkdir -p $out
      cp -R build/html/* $out/
    '';

    shellHook = ''
      export RELENG_DOCS_VERSION=${version}
    '';

    passthru.taskclusterGithubTasks =
      map (branch: mkTaskclusterGithubTask { inherit name src_path branch; }) [ "master" "staging" "production" ];

    passthru.update  = writeScript "update-${name}" ''
      pushd src/${name}
      ${pypi2nix}/bin/pypi2nix -v \
        -V 3.5 \
        -r requirements.txt
      popd
    '';

   };
in self
