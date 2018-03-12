# From https://gist.github.com/benley/e4a91e8425993e7d6668

# Heavily cribbed from the equivalent NixOS login script.
# This should work better with multi-user nix setups.

export USER=`whoami`
export NIXPKGS_CONFIG="/etc/nix/nixpkgs-config.nix"
export NIX_OTHER_STORES="/run/nix/remote-stores/\*/nix"
export NIX_USER_PROFILE_DIR="/nix/var/nix/profiles/per-user/$USER"
if [ -z "$NIX_PATH" ]; then
    export NIX_PATH="/nix/var/nix/profiles/per-user/root/channels"
fi
export PATH="$HOME/.nix-profile/bin:$HOME/.nix-profile/sbin:/nix/var/nix/profiles/default/bin:/nix/var/nix/profiles/default/sbin:$PATH"

# Use the nix daemon for multi-user builds
if [ "$USER" != root -o ! -w /nix/var/nix/db ]; then
  export NIX_REMOTE=daemon
fi

# Set up the per-user profile.
mkdir -m 0755 -p "$NIX_USER_PROFILE_DIR"
if test "$(stat --printf '%u' "$NIX_USER_PROFILE_DIR")" != "$(id -u)"; then
    echo "WARNING: bad ownership on $NIX_USER_PROFILE_DIR" >&2
fi

if [ -w "$HOME" ]; then
  # Set the default profile.
  if ! [ -L "$HOME/.nix-profile" ]; then
    if [ "$USER" != root ]; then
      ln -s "$NIX_USER_PROFILE_DIR/profile" "$HOME/.nix-profile"
    else
      # Root installs in the system-wide profile by default.
      ln -s /nix/var/nix/profiles/default "$HOME/.nix-profile"
    fi
  fi

  # Create the per-user garbage collector roots directory.
  NIX_USER_GCROOTS_DIR=/nix/var/nix/gcroots/per-user/$USER
  mkdir -m 0755 -p "$NIX_USER_GCROOTS_DIR"
  if test "$(stat --printf '%u' "$NIX_USER_GCROOTS_DIR")" != "$(id -u)"; then
    echo "WARNING: bad ownership on $NIX_USER_GCROOTS_DIR" >&2
  fi

  # Set up a default Nix expression from which to install stuff.
  if [ ! -e "$HOME/.nix-defexpr" -o -L "$HOME/.nix-defexpr" ]; then
    rm -f "$HOME/.nix-defexpr"
    mkdir "$HOME/.nix-defexpr"
    if [ "$USER" != root ]; then
        ln -s /nix/var/nix/profiles/per-user/root/channels "$HOME/.nix-defexpr/channels_root"
    fi
  fi

  # Subscribe the to the Nixpkgs channel by default.
  if [ ! -e "$HOME/.nix-channels" ]; then
      echo "https://nixos.org/channels/nixpkgs-unstable nixpkgs" > "$HOME/.nix-channels"
  fi

  # Prepend ~/.nix-defexpr/channels/nixpkgs to $NIX_PATH so that
  # <nixpkgs> paths work when the user has fetched the Nixpkgs
  # channel.
  # XXX: in docker we want to use specific nixpkgs which is at /etc/nix/nixpkgs
  if [ ! -f /.dockerenv ]; then
    export NIX_PATH="nixpkgs=$HOME/.nix-defexpr/channels/nixpkgs${NIX_PATH:+:$NIX_PATH}"
  fi

  # Make sure nix-channel --update works
  SSL_CERT_FILE=/nix/var/nix/profiles/default/etc/ssl/certs/ca-bundle.crt
  CURL_CA_BUNDLE=$SSL_CERT_FILE
fi
