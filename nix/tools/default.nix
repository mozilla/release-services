{ releng_pkgs }:

let
  inherit (releng_pkgs.pkgs) writeScript stdenv makeWrapper;
in {

  pypi2nix = import ./pypi2nix.nix { inherit releng_pkgs; } // {
    update = releng_pkgs.lib.updateFromGitHub {
      owner = "garbas";
      repo = "pypi2nix";
      branch = "master";
      path = "nix/tools/pypi2nix.json";
    };
  };

  awscli = (import ./awscli.nix { inherit (releng_pkgs) pkgs; }).packages."awscli" // {
    update = writeScript "update-tools-awscli" ''
      pushd nix/tools
      ${releng_pkgs.tools.pypi2nix}/bin/pypi2nix --basename "awscli" -V "3.5" -e awscli -v
      popd
    '';
  };

  taskcluster-hooks = 
    let
      python = import ./hooks.nix { inherit (releng_pkgs) pkgs; };
      python_path =
        "${python.__old.python}/${python.__old.python.sitePackages}:" +
        (builtins.concatStringsSep ":"
          (map (pkg: "${pkg}/${python.__old.python.sitePackages}")
               (builtins.attrValues python.packages)
          )
        );
    in stdenv.mkDerivation {
      name = "taskcluster-hooks";
      buildInputs = [ makeWrapper python.__old.python ];
      buildCommand = ''
        mkdir -p $out/bin
        cp ${./hooks.py} $out/bin/taskcluster-hooks
        chmod +x $out/bin/taskcluster-hooks
        echo "${python.__old.python}"
        patchShebangs $out/bin/taskcluster-hooks
        wrapProgram $out/bin/taskcluster-hooks \
          --set PYTHONPATH "${python_path}" \
          --set LANG "en_US.UTF-8" \
          --set LOCALE_ARCHIVE ${releng_pkgs.pkgs.glibcLocales}/lib/locale/locale-archive
      '';
      passthru.update = writeScript "update-tools-taskcluster-hooks" ''
        pushd nix/tools
        ${releng_pkgs.tools.pypi2nix}/bin/pypi2nix --basename "hooks" -V "3.5" -r hooks.txt -v
        popd
      '';
    };

  push = (import ./push.nix { inherit (releng_pkgs) pkgs; }).packages."push" // {
    update = writeScript "update-tools-push" ''
      pushd nix/tools
      ${releng_pkgs.tools.pypi2nix}/bin/pypi2nix --basename "push" -V "3.5" -r push.txt -v
      popd
    '';
  };

  node2nix = import ./node2nix.nix { inherit releng_pkgs; } // {
    update = releng_pkgs.lib.updateFromGitHub {
      owner = "svanderburg";
      repo = "node2nix";
      branch = "master";
      path = "nix/tools/node2nix.json";
    };
  };

  elm2nix = import ./elm2nix.nix { inherit releng_pkgs; };

  mysql2pgsql = (import ./mysql2pgsql.nix { inherit (releng_pkgs) pkgs; }).packages."py-mysql2pgsql" // {
    update = writeScript "update-tools-mysql2pgsql" ''
      pushd nix/tools
      ${releng_pkgs.tools.pypi2nix}/bin/pypi2nix --basename "mysql2pgsql" -V "2.7" -e py-mysql2pgsql -E "postgresql mysql.lib" -v
      popd
    '';
  };

  createcert = (import ./createcert.nix { inherit releng_pkgs; }) // {
    update = null;
  };

  mercurial = import ./mercurial.nix { inherit releng_pkgs; };

}
