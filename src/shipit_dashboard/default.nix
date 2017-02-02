{ releng_pkgs
}: 

let

  inherit (releng_pkgs.lib) mkBackend mkTaskclusterHook filterSource;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  releng_common = import ./../../lib/releng_common {
    inherit releng_pkgs python;
    extras = ["api" "auth" "cors" "log" "db" "security" ];
  };

  self = mkBackend rec {
    inherit python releng_common;
    production = true;
    name = "shipit_dashboard";
    version = fileContents ./../../VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      [ python.packages."flake8"
        python.packages."pytest"
        python.packages."ipdb"
        python.packages."responses"
      ];
    passthru = {
      update = writeScript "update-${name}" ''
        pushd src/${name}
        ${pypi2nix}/bin/pypi2nix -v \
         -V 3.5 \
         -E "postgresql" \
				 -s "six packaging appdirs" \
         -r ../../lib/releng_common/requirements-dev.txt \
         -r requirements.txt \
         -r requirements-dev.txt \
         -r requirements-nix.txt
        popd
      '';
    };
  };

in self
