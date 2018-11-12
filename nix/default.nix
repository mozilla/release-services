let
  requiredNixVersion = "2.0pre";
  pkgs' = import <nixpkgs> {};
  nixpkgs-json = builtins.fromJSON (builtins.readFile ./nixpkgs.json);
  src-nixpkgs = pkgs'.fetchFromGitHub { inherit (nixpkgs-json) owner repo rev sha256; };
  src-nixpkgs-mozilla = pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs-mozilla.json));
in

# ensure we are using correct version of Nix
if ! builtins ? nixVersion || builtins.compareVersions requiredNixVersion builtins.nixVersion >= 0
then abort "mozilla/release-services requires Nix >= ${requiredNixVersion}, please upgrade."
else

{ pkgs ? import src-nixpkgs {
    overlays = [
      (import "${src-nixpkgs-mozilla}/rust-overlay.nix")
      (import "${src-nixpkgs-mozilla}/firefox-overlay.nix")
      (import ./overlay/default.nix)
    ];
  }
}:

let

  filter_dirs = x:
    builtins.filter
      (p: (builtins.getAttr p x) == "directory")
      (builtins.attrNames x);

  src_dir = ./../src;
  level_one_dirs = filter_dirs (builtins.readDir src_dir);
  level_two_dirs = pkgs.lib.flatten (builtins.map (x: builtins.map
                                                        (y: "${x}/${y}")
                                                        (filter_dirs (builtins.readDir "${src_dir}/${x}")))
                                     level_one_dirs);

  releng_pkgs = {
    inherit pkgs;
    lib = import ./lib/default.nix { inherit releng_pkgs; };
    tools = import ./tools/default.nix { inherit releng_pkgs; };
    gecko-env = import ./gecko_env.nix { inherit releng_pkgs; };
    elmPackages = pkgs.elmPackages.override { nodejs = pkgs."nodejs-6_x"; };


    "postgresql" =
      releng_pkgs.lib.mkProject
        { project_name = builtins.elemAt (pkgs'.lib.splitString "-" pkgs'.postgresql.name) 0;
          version = builtins.elemAt (pkgs'.lib.splitString "-" pkgs'.postgresql.name) 1;
          name = "${pkgs.postgresql.name}-env";
          buildInputs = [ pkgs.postgresql95 ];
          mkDerivation = pkgs.stdenv.mkDerivation;
          passthru = {
            package = pkgs.postgresql95;
          };
        };

    "redis" =
      releng_pkgs.lib.mkProject
        { project_name = builtins.elemAt (pkgs'.lib.splitString "-" pkgs'.redis.name) 0;
          version = builtins.elemAt (pkgs'.lib.splitString "-" pkgs'.redis.name) 1;
          name = "${pkgs.redis.name}-env";
          buildInputs = [ pkgs.redis ];
          mkDerivation = pkgs.stdenv.mkDerivation;
          package = pkgs.redis;
          passthru.package = pkgs.redis;
        };

    "please-cli" = import ./../lib/please_cli { inherit releng_pkgs; };
    # TODO: backend_common_example = import ./../lib/backend_common/example { inherit releng_pkgs; };
    "frontend-common-example" = import ./../lib/frontend_common/example { inherit releng_pkgs; };

  } // (
    # list projects (folders in src/ folder with default.nix) and imports them
    builtins.listToAttrs (
      builtins.map
        (project: { name = builtins.replaceStrings ["_"] ["-"] project;
                    value = import (src_dir + "/${project}/default.nix") { inherit releng_pkgs; };
                  })
        (builtins.filter
          (project: builtins.pathExists (src_dir + "/${project}/default.nix"))
          (level_one_dirs ++ level_two_dirs)))
    );

in releng_pkgs
