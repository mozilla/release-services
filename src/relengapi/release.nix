{ relengapi ? { outPath = ./.; name = "relengapi"; }
, supportedSystems ? [ "x86_64-linux" ]
}:

let

  pkgs = import <nixpkgs> {};

  pkgFor = system: develop:
    if builtins.elem system supportedSystems
      then import ./default.nix {
        inherit develop relengapi;
        pkgs = import pkgs.path { inherit system; };
      }
      else abort "Unsupported system type: ${system}";

  dockerFor = system: develop:
    let
      dockerImage = pkgs.dockerTools.buildImage {
        name = "docker-relengapi-${version}";
        tag = version;
        fromImage = null;
        contents = with pkgs; [ busybox (pkgFor system false) ];
        config = {
          Env = [ "PATH=/bin" ];
          WorkingDir = "/data";
          Volumes = {
            "/data" = {};
          };
        };
      };
    in pkgs.runCommand "docker-relengapi-${version}" {} ''
      mkdir -p $out/nix-support
      ln -s ${dockerImage} $out/docker.tar.gz
      echo "file binary-dist $out/docker.tar.gz" > $out/nix-support/hydra-build-products
    '';

  forEach = f: develop:
    builtins.listToAttrs (map (system:
      { name = system;
        value = pkgs.lib.hydraJob (f system develop);
      }) supportedSystems);

  version = pkgs.lib.removeSuffix "\n" (builtins.head (pkgs.lib.splitString "\n" (builtins.readFile ./VERSION)));

  self = {

    tarball = pkgs.runCommand "relengapi-${version}-tarball"
      { buildInputs = with pkgs.pythonPackages; [ python setuptools ]; }
      ''
        python ${relengapi}/setup.py sdist --formats=gztar

        mkdir -p $out
        mv dist/relengapi-${version}.tar.gz $out/

        mkdir -p $out/nix-support
        echo "file source-dist $out/relengapi-${version}.tar.gz" > $out/nix-support/hydra-build-products
      '';

    build = forEach pkgFor false;
    build_develop = forEach pkgFor true;
    docker = forEach dockerFor false;

    release = pkgs.releaseTools.aggregate {
      name = "relengapi-${version}";
      meta.description = "Aggregate job containing the release-critical jobs.";
      constituents = [ self.tarball ] ++
        (map (x: builtins.attrValues x) (with self; [
          build build_develop docker ]));
    };

  };

in self
