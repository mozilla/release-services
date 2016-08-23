{ releng_pkgs }:

let
  inherit (releng_pkgs.pkgs) writeScriptBin;
in {

  pypi2nix = import ./pypi2nix.nix { inherit releng_pkgs; } // {
    updateSrc = releng_pkgs.lib.updateFromGitHub {
      owner = "garbas";
      repo = "pypi2nix";
      branch = "master";
      path = "nix/tools/pypi2nix.json";
    };
  };

  awscli = (import ./awscli.nix { inherit (releng_pkgs) pkgs; }).packages."awscli" // {
    updateSrc = writeScriptBin "update" ''
      pushd nix/tools
      ${releng_pkgs.tools.pypi2nix}/bin/pypi2nix --basename "awscli" -V "3.5" -e awscli -v
      popd
    '';
  };

  node2nix = import ./node2nix.nix { inherit releng_pkgs; } // {
    updateSrc = releng_pkgs.lib.updateFromGitHub {
      owner = "svanderburg";
      repo = "node2nix";
      branch = "master";
      path = "nix/tools/node2nix.json";
    };
  };

  elm2nix = import ./elm2nix.nix { inherit releng_pkgs; };

  mysql2sqlite = import ./mysql2sqlite.nix { inherit releng_pkgs; } // {
    updateSrc = releng_pkgs.lib.updateFromGitHub {
      owner = "dumblob";
      repo = "mysql2sqlite";
      branch = "master";
      path = "nix/tools/mysql2sqlite.json";
    };
  };

  mysql2pgsql = (import ./mysql2pgsql.nix { inherit (releng_pkgs) pkgs; }).packages."py-mysql2pgsql" // {
    updateSrc = writeScriptBin "update" ''
      pushd nix/tools
      ${releng_pkgs.tools.pypi2nix}/bin/pypi2nix --basename "mysql2pgsql" -V "2.7" -e py-mysql2pgsql -E "postgresql mysql.lib" -v
      popd
    '';
  };

}
