let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json))) {}
, prefix ? "services-"
}:

let

  releng_pkgs = import ./default.nix { inherit pkgs; };

  inherit (releng_pkgs.lib) packagesWith;
  inherit (releng_pkgs.pkgs.lib) flatten;

in pkgs.writeText "taskcluster_hooks.json"
  ( builtins.toJSON ( builtins.listToAttrs ( flatten
    ( map (pkg: map (hookId: { name = "${prefix}${(builtins.parseDrvName pkg.name).name}-${hookId}";
                               value = builtins.getAttr hookId pkg.taskclusterHooks;
                             })
                    (builtins.attrNames pkg.taskclusterHooks)
          )
          (packagesWith "taskclusterHooks" releng_pkgs)
    )
  )))
