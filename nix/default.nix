let
  requiredNixVersion = "2.0pre";
  pkgs' = import <nixpkgs> {};
  nixpkgs-json = builtins.fromJSON (builtins.readFile ./nixpkgs.json);
  src-nixpkgs = pkgs'.fetchFromGitHub { inherit (nixpkgs-json) owner repo rev sha256; };
  src-nixpkgs-mozilla = pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs-mozilla.json));
in

# ensure we are using correct version of Nix
if ! builtins ? nixVersion || builtins.compareVersions requiredNixVersion builtins.nixVersion >= 0
then abort "mozilla-releng/services requires Nix >= ${requiredNixVersion}, please upgrade."
else

{ pkgs ? import src-nixpkgs {
    overlays = [
      (import "${src-nixpkgs-mozilla}/rust-overlay.nix")
      (import "${src-nixpkgs-mozilla}/firefox-overlay.nix")
    ];
  }
}:

let

  src_dir = ./../src;
  releng_pkgs = {
    inherit pkgs;
    lib = import ./lib/default.nix { inherit releng_pkgs; };
    tools = import ./tools/default.nix { inherit releng_pkgs; };
    gecko-env = import ./gecko_env.nix { inherit releng_pkgs; };
    elmPackages = pkgs.elmPackages.override { nodejs = pkgs."nodejs-6_x"; };

    "postgresql" =
      pkgs.stdenv.mkDerivation
        { name = "${pkgs.postgresql.name}-env";
          buildInputs = [ pkgs.postgresql95 ];
          passthru.package = pkgs.postgresql95;
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
		  (builtins.attrNames (builtins.readDir src_dir))))
  );

in releng_pkgs
