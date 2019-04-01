{ releng_pkgs
}:

let

  inherit (releng_pkgs.pkgs) fetchFromGitHub;

  src-scriptworker-shipitscript = fetchFromGitHub {
    owner = "mozilla-releng";
    repo = "shipitscript";
    rev = "5db546d7916630a62f8f9f9719b2a3d3a7fa1870";
    sha256 = "05caga08jd5l2np6h1zi8lx4q89b6pcsj7vs9iv3m3db32d1dkqh";
  };

in import "${src-scriptworker-shipitscript}/nix" { inherit (releng_pkgs) pkgs; }
