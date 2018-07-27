{ releng_pkgs
}:
let
  inherit (releng_pkgs.pkgs.lib) fileContents;
in
releng_pkgs.lib.mkYarnFrontend {
  src = ./.;
}
