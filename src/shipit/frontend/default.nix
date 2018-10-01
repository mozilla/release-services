{ releng_pkgs
}:

releng_pkgs.lib.mkYarnFrontend {
  src = ./.;
  src_path = "src/shipit/frontend";
  csp = "default-src 'none'; img-src 'self' *.gravatar.com data:; script-src 'self' 'unsafe-inline' https://cdn.auth0.com; style-src 'self'; font-src 'self'; frame-src 'self' https://auth.mozilla.auth0.com;";
  extraBuildInputs = with releng_pkgs.pkgs; [
    libpng
    libpng.dev
    pkgconfig
  ];
}
