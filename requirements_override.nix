{ pkgs, python }:

self: super: {

  "flask-restplus" = python.overrideDerivation super."flask-restplus" (old: {
    # https://github.com/noirbizarre/flask-restplus/pull/165
    name = "flask-restplus-0.9.3.dev5d20449e";
    src = pkgs.fetchFromGitHub {
      owner = "stevezau";
      repo = "flask-restplus";
      rev = "5d20449ef13a3d3d3051438fc408534a6bb9362f";
      sha256= "0f1z7qiq556vn60yr75kx4s2whf5qazvk2b4na887fnwlpa2c9q3";
    };
  });
}
