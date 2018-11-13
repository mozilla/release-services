{ releng_pkgs
}:
let
  inherit (releng_pkgs.pkgs.lib) fileContents;

in releng_pkgs.lib.mkYarnFrontend {
  project_name = "shipit/frontend";
  version = fileContents ./VERSION;
  src = ./.;
  csp = "default-src 'none'; img-src 'self' *.gravatar.com data:; script-src 'self' 'unsafe-inline' https://cdn.auth0.com; style-src 'self'; font-src 'self'; frame-src 'self' https://auth.mozilla.auth0.com;";
  extraBuildInputs = with releng_pkgs.pkgs; [
    libpng
    libpng.dev
    pkgconfig
  ];
}
