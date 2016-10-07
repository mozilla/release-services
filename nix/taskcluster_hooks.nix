let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json))) {}
, prefix ? "services-"
, branch
}:

let

  releng_pkgs = import ./default.nix { inherit pkgs; };

  inherit (releng_pkgs.lib) packagesWith;
  inherit (releng_pkgs.pkgs.lib) flatten;

in pkgs.writeText "taskcluster_hooks.json"
   (builtins.toJSON (builtins.listToAttrs (flatten
     (map (pkg: let
                  hooks' = pkg.taskclusterHooks;
                  hooks = if builtins.hasAttr branch pkg.taskclusterHooks
                          then builtins.getAttr branch pkg.taskclusterHooks
                          else {};
                in
                  map (hookId: { name = "${prefix}${branch}-${(builtins.parseDrvName pkg.name).name}-${hookId}";
                                 value = builtins.getAttr hookId (builtins.getAttr branch pkg.taskclusterHooks);
                               }
                      )
                      (builtins.attrNames hooks)
          )
          (packagesWith "taskclusterHooks" releng_pkgs)
     )
   )))
