{ releng_pkgs }:

let

  pythonTools = import ./requirements.nix { inherit (releng_pkgs) pkgs; };


in {

  awscli = pythonTools.packages."awscli";

  aws-shell = pythonTools.packages."aws-shell";

  node2nix = import ./node2nix.nix { inherit releng_pkgs; };

  elm2nix = import ./elm2nix.nix { inherit releng_pkgs; };

  mysql2sqlite = import ./mysql2sqlite.nix { inherit releng_pkgs; };

  #mysql2postgresql = import ./mysql2sqlite.nix { inherit releng_pkgs; };
}
