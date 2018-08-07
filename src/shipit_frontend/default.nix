{ releng_pkgs
}:

releng_pkgs.lib.mkYarnFrontend {
  src = ./.;
  extraBuildInputs = with releng_pkgs.pkgs; [
    libpng
    libpng.dev
    pkgconfig
  ];
}
