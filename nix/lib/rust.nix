pkgs:
{ crates_json ? null
, rust ? pkgs.rustStable
}:

let

  crates_json_default = pkgs.lib.importJSON ./crates.json;
  crates_json' = 
    if crates_json == null
      then crates_json_default
      else crates_json;
  crates_version = "${builtins.substring 0 10 crates_json'.date}";
  crates_src = pkgs.fetchFromGitHub
    { owner = "rust-lang";
      repo = "crates.io-index";
      rev = crates_json'.rev;
      sha256 = crates_json'.sha256;
    };

  rustRegistry = pkgs.runCommand "rustRegistry-${crates_version}-${builtins.substring 0 7 crates_json'.rev}" { inherit crates_src; } ''
    # For some reason, cargo doesn't like fetchgit's git repositories, not even
    # if we set leaveDotGit to true, set the fetchgit branch to 'master' and clone
    # the repository (tested with registry rev
    # 965b634156cc5c6f10c7a458392bfd6f27436e7e), failing with the message:
    #
    # "Target OID for the reference doesn't exist on the repository"
    #
    # So we'll just have to create a new git repository from scratch with the
    # contents downloaded with fetchgit...
    mkdir -p $out
    cp -r ${crates_src}/* $out/
    cd $out
    git="${pkgs.git}/bin/git"
    $git init
    $git config --local user.email "example@example.com"
    $git config --local user.name "example"
    $git add .
    $git commit -m 'Rust registry commit'
    touch $out/touch . "$out/.cargo-index-lock"
  '';

in pkgs.recurseIntoAttrs (pkgs.lib.fix (self:
  let
    callPackage = pkgs.newScope self;
  in {
      inherit rust rustRegistry;
      buildRustPackage = callPackage "${pkgs.path}/pkgs/build-support/rust" {
        inherit rust;
      };
    }
))
