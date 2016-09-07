{ contents ? []
}:

let
  pkgs = import <nixpkgs> {};
  pkgsSrc = builtins.fromJSON (builtins.readFile ./nixpkgs.json);
  #pkgs = import (pkgs'.fetchFromGitHub pkgsSrc) {};

  passwd = ''
    root:x:0:0::/root:/run/current-system/sw/bin/bash
    nixbld1:x:30001:30000::/var/empty:/bin/nologin
    nixbld2:x:30002:30000::/var/empty:/bin/nologin
  '';
  group = ''
    root:x:0:
    nixbld:x:30000:nixbld1,nixbld2
  '';

  profile = pkgs.buildEnv {
    name = "docker-environment";
    paths = with pkgs; [ git nix busybox ];
  };

  profile_closure = pkgs.runCommand "profile-closure"
    { exportReferencesGraph = [ "closure1" profile "closure2" pkgs.cacert ];
      buildInputs = [ pkgs.perl ];
    }
    ''
      mkdir -p $out
      echo $(perl ${pkgs.pathsFromGraph} ./closure1 ./closure2) > $out/paths
      printRegistration=1 perl ${pkgs.pathsFromGraph} ./closure1 ./closure2 > $out/reginfo
     '';

in pkgs.dockerTools.buildImage {
  name = "releng-services-init";
  tag = pkgsSrc.rev;
  fromImage = null;
  #contents = with pkgs; [ busybox gnumake nix.out cacert ];
  extraCommands = ''
    mkdir -p etc var tmp root/.nix-defexpr nix/var/nix/profiles/per-user/root nix/store

    ln -s ${profile} nix/var/nix/profiles/per-user/root/profile-1-link
    ln -s nix/var/nix/profiles/per-user/root/profile-1-link nix/var/nix/profiles/per-user/root/profile
    ln -s nix/var/nix/profiles/per-user/root/profile root/.nix-profile

    cat > etc/passwd <<EOL
    ${passwd}
    EOL

    cat > etc/group <<EOL
    ${group}
    EOL

    for item in `cat ${profile_closure}/paths`; do
      cp -dR $item nix/store
    done

    cp ${profile_closure}/reginfo reginfo

    ls -la
    exit 123
  '';
  config = {
    #Cmd = [ "bash" ];
    Env = [
      "PATH=/bin"
      "TMPDIR=/tmp"
      "GIT_SSL_CAINFO=/root/.nix-profile/etc/ssl/certs/ca-bundle.crt"
      "SSL_CERT_FILE=/root/.nix-profile/etc/ssl/certs/ca-bundle.crt"
      "PATH=/root/.nix-profile/bin:/root/.nix-profile/sbin"
      "MANPATH=/root/.nix-profile/share/man:/run/current-system/sw/share/man"
      "NIX_PATH=nixpkgs=https://github.com/${pkgsSrc.owner}/${pkgsSrc.repo}/archive/${pkgsSrc.rev}.tar.gz"
    ];
  };
}
