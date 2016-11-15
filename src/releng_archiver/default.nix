{ releng_pkgs
}: 

let

  inherit (releng_pkgs.lib) mkBackend filterSource;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  releng_common = import ./../../lib/releng_common {
    inherit releng_pkgs python;
    extras = ["api" "auth" "cors" "log" "db" ];
  };

  self = mkBackend rec {
    inherit python;
    name = "releng_archiver";
    version = fileContents ./../../VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      [ python.packages."flake8"
        python.packages."pytest"
        python.packages."ipdb"
      ];
    propagatedBuildInputs =
      [ releng_common
      ];
    passthru = {
      update = writeScript "update-${name}" ''
        pushd src/${name}
        ${pypi2nix}/bin/pypi2nix -v \
         -V 3.5 \
         -E "postgresql" \
         -r requirements.txt \
         -r requirements-dev.txt \
         -r requirements-nix.txt 
        popd
      '';
    };
  };

in self
