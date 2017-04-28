let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json))) {}
, prefix ? "services"
, branch
, app
}:

let

  releng_pkgs = import ./default.nix { inherit pkgs; };

  inherit (releng_pkgs.lib) packagesWith;
  inherit (releng_pkgs.pkgs.lib) flatten;

  pkg = if builtins.hasAttr app releng_pkgs.apps
        then builtins.getAttr app releng_pkgs.apps
        else null;

  hooks = if pkg == null || ! builtins.hasAttr "taskclusterHooks" pkg then {}
          else if builtins.hasAttr branch pkg.taskclusterHooks
          then builtins.getAttr branch pkg.taskclusterHooks
          else {};

  hooks_json = builtins.listToAttrs
    (map (hookId: { name = "${prefix}-${branch}-${app}-${hookId}";
                    value = builtins.getAttr hookId (builtins.getAttr branch pkg.taskclusterHooks);
                  }
         )
         (builtins.attrNames hooks));

in pkgs.writeText "taskcluster_hooks.json" (builtins.toJSON hooks_json)
