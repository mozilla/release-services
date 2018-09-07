{ releng_pkgs
}:

releng_pkgs.lib.mkYarnFrontend {
  src = ./.;
  csp = "default-src 'none'; img-src 'self' *.gravatar.com data:; script-src 'self' 'unsafe-inline'; style-src 'self'; font-src 'self'; frame-src https://auth.mozilla.auth0.com;";
  src_path = "src/shipit/frontend";
  extraBuildInputs = with releng_pkgs.pkgs; [
    libpng
    libpng.dev
    pkgconfig
  ];
}
