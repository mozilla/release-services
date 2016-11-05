{ releng_pkgs
}: 

let

  inherit (releng_pkgs.lib) mkBackend filterSource mysql2sqlite mysql2postgresql;
  inherit (releng_pkgs.pkgs) writeScript;
  inherit (releng_pkgs.pkgs.lib) removeSuffix;
  inherit (releng_pkgs.tools) pypi2nix;

  self = mkBackend rec {
    name = "releng_treestatus";
    version = removeSuffix "\n" (builtins.readFile ./../../VERSION);
    python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
    src = filterSource ./. {
      exclude = [
        "/${name}.egg-info"
        "/releng_common.egg-info"
      ];
      include = [
        "/VERSION"
        "/${name}"
        "/releng_common"
        "/tests"
        "/MANIFEST.in"
        "/settings.py"
        "/setup.py"
        "/requirements.txt"
      ];
    };
    srcs = [
      "./../../lib/releng_common"
      "./../${name}"
    ];
    buildRequirements = [ ./requirements-dev.txt ];
    propagatedRequirements = [ ./../../lib/releng_common/requirements.txt ./requirements.txt ./requirements-prod.txt ];
    passthru = {
      mysql2sqlite = mysql2sqlite { inherit name; };
      mysql2postgresql = mysql2postgresql { inherit name; };
      update = writeScript "update-${name}" ''
        pushd src/${name}
        ${pypi2nix}/bin/pypi2nix -v \
         -V 3.5 \
         -E "postgresql" \
         -r requirements.txt \
         -r requirements-dev.txt \
         -r requirements-prod.txt 
        popd
      '';
    };
  };

in self
