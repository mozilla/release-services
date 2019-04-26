{ releng_pkgs
}:

let

  inherit (releng_pkgs.pkgs) fetchFromGitHub;

  src-scriptworker-shipitscript = fetchFromGitHub {
    owner = "mozilla-releng";
    repo = "shipitscript";
    rev = "1aedbc50ffbbfa2f8436ae35a94c2e5955bfe06a";
    sha256 = "148jph6n07bav1m7gwg3hxk0yagvsw3b7fp0mwm6phli7l6ipfbs";
  };

in import "${src-scriptworker-shipitscript}/nix" { inherit (releng_pkgs) pkgs; }
