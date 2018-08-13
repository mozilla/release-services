{ releng_pkgs
}:

releng_pkgs.lib.mkYarnFrontend {
  src = ./.;
  src_path = "src/shipit/frontend";
  extraBuildInputs = with releng_pkgs.pkgs; [
    autoconf
    automake
    libpng
    libpng.dev
    libtool
    pkgconfig
    nasm
  ];
}
