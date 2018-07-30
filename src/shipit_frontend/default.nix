{ releng_pkgs
}:

releng_pkgs.lib.mkYarnFrontend {
  src = ./.;
}
