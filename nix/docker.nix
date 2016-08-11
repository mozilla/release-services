let pkgs' = import <nixpkgs> {}; in
{ pkgs ? import (pkgs'.fetchFromGitHub (builtins.fromJSON (builtins.readFile ./nixpkgs.json))) {}
}:

let

  releng_pkgs = import ./default.nix { inherit pkgs; };

  forEach = func : pkgs':
    builtins.listToAttrs 
      (map
        (name: { inherit name;
                 value = func (builtins.getAttr name pkgs');
               }
        )
        (builtins.attrNames pkgs')
      );

  docker = pkg:
    let
      dockerConfig = pkgs.lib.optionalAttrs (builtins.hasAttr "dockerConfig" pkg) pkg.dockerConfig;
      dockerContents = pkgs.lib.optionals (builtins.hasAttr "dockerContents" pkg) pkg.dockerContents;
      dockerEnvs = pkgs.lib.optionals (builtins.hasAttr "dockerEnvs" pkg) pkg.dockerEnvs;
      pkgName = builtins.parseDrvName pkg.name;
    in pkgs.dockerTools.buildImage {
      name = pkgName.name;
      tag = pkgName.version;
      fromImage = null;
      contents = with pkgs; [ busybox pkg ] ++ dockerContents;
      config = {
        Env = [ "PATH=/bin" ] ++ dockerEnvs;
      } // dockerConfig;
    };

in forEach docker releng_pkgs
