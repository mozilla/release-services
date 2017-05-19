#!/usr/bin/env bash
set -e

# Uncomment for debugging
#set -x

CONF=/etc/nix/nix.conf
GROUP=nixbld

function check_dep {
	command -v "$1" >/dev/null 2>&1 || {
		echo >&2 "This script required $1 but it's not installed. Aborting.";
		exit 1;
	}
}

function as_root {
	# Run command in a root shell
	sudo bash -c "$@"
}

function has_single_user_install {
	# Check if there is an existing single user install
	if [[ -d /nix && -e /home/$USER/.nix-profile && -d /home/$USER/.nix-profile/bin ]] ; then
		return 0
	else
		return 1
	fi
}

function has_multi_user_install {
	# Check if there is an existing multi user install
	if [[ ! -f /etc/nix/nix.conf ]] ; then
		return 1
	fi
	if ! grep -Fxq 'build-use-sandbox = true' /etc/nix/nix.conf ; then
		return 1
	fi
	if ! pgrep -x 'nix-daemon' ; then
		return 1
	fi

	return 0
}

function update_nix {
	# Update nix install as root user
	as_root "
	source /etc/nix/nix-profile.sh
	nix-channel --update
	nix-env \
		-p /nix/var/nix/profiles/default \
		-f /root/.nix-defexpr/channels/nixpkgs/ \
		-iA nix
	nix-env -iA nixpkgs.nix nixpkgs.cacert"
}

# Check all dependencies
check_dep sudo
check_dep curl
check_dep grep
check_dep pgrep
check_dep groupadd
check_dep useradd

# Check we run as standard user
if [[ $EUID -eq 0 ]] ; then
	echo "This script must not be run as root."
	exit 1
fi

# Check we have sudo capabilities
echo "Testing sudo access"
if ! sudo bash -c 'echo $UID > /dev/null'; then
	echo "You do not seem to have sudo access. Aborting."
	exit 1
fi

# Check for init service : systemd or upstart
INIT_PROC=$(ps -p 1)
if [[ $INIT_PROC == *systemd* ]] ; then
	INITD=systemd
elif [[ $INIT_PROC == *init* ]] ; then
	INITD=upstart
else
	echo "System does not use systemd or upstart. Weird."
	exit 1
fi
echo "Detected init service: $INITD"

# Single user install
if has_single_user_install ; then
	echo "Skipping Step 1: Nix is already installed as single user."
else
	echo "1. Installing Nix as single user mode"
	sudo mkdir -m 0755 /nix
	sudo chown "$USER" /nix
	curl https://nixos.org/nix/install | sh
fi

# Update for existing multi user install
if has_multi_user_install ; then

	echo "Skipping install steps: just update Nix install"
	sudo chown -R "$USER":"$USER" "/nix/var/nix/profiles/per-user/$USER" "/nix/var/nix/gcroots/per-user/$USER"
	update_nix

	# Install packages to test it out
	nix-env -iA nixpkgs.git
	nix-env -iA nixpkgs.gnumake

	echo "Update done."
	exit 0 # Finish gracefully
fi

echo "2. Add custom binary cache"
sudo mkdir -p /etc/nix
as_root "echo 'binary-caches = https://cache.mozilla-releng.net https://cache.nixos.org' > $CONF"

echo "3. Add build group and users for multi user mode"
# Create group & users only when they do not exist
getent group "$GROUP" > /dev/null || sudo groupadd -r $GROUP
for n in $(seq 1 10); do
	username=$GROUP$n
	id -u "$username" 1> /dev/null 2>&1 || sudo useradd \
		-c "Nix build user $n" \
		-d /var/empty \
		-g "$GROUP" \
		-G "$GROUP" \
		-M -N -r -s "$(which nologin)" \
    "$username";
done

as_root "echo \"build-users-group = $GROUP\" >> $CONF"
sudo chown -R root:"$GROUP" /nix
sudo chmod 1777 /nix/var/nix/profiles/per-user
sudo mkdir -m 1777 -p /nix/var/nix/gcroots/per-user

echo "4. Enabling sandbox mode"
as_root "echo 'build-use-sandbox = true' >> $CONF"
sudo mkdir -p /nix/var/nix/profiles
as_root "/home/$USER/.nix-profile/bin/nix-channel --add https://nixos.org/channels/nixpkgs-unstable"
as_root "/home/$USER/.nix-profile/bin/nix-channel --update"
as_root "/home/$USER/.nix-profile/bin/nix-env -iA nixpkgs.bash -p /nix/var/nix/profiles/sandbox"

bash_path=$(realpath /nix/var/nix/profiles/sandbox/bin/bash)
bash_deps=$(sudo "/home/$USER/.nix-profile/bin/nix-store" -qR "$bash_path" | tr '\n' ' ')
as_root "echo \"build-sandbox-paths = /bin/sh=$bash_path $bash_deps\" >> $CONF"

echo "5. Migrating from single user to multi user mode"
rm "$HOME/.nix-profile"
rm -r "$HOME/.nix-defexpr"
sudo cp -r /nix/var/nix/profiles/default-*-link "/nix/var/nix/profiles/per-user/$USER/profile-1-link"

echo "6. Add nix-daemon service"
if [[ $INITD == "systemd" ]] ; then
    cat <<'EOF' | sudo tee /etc/systemd/system/nix-daemon.service
[Unit]
Description=Nix daemon

[Service]
Environment=SSL_CERT_FILE=/nix/var/nix/profiles/default/etc/ssl/certs/ca-bundle.crt
ExecStart=/nix/var/nix/profiles/default/bin/nix-daemon $EXTRA_OPTS
IgnoreSIGPIPE=false
KillMode=process

[Install]
WantedBy=multi-user.target
EOF

	sudo mkdir -p /nix/var/nix/daemon-socket
	sudo systemctl enable nix-daemon
	sudo systemctl start nix-daemon

elif [[ $INITD == "upstart" ]] ; then
    cat <<'EOF' | sudo tee /etc/init/nix-daemon.conf
description "Nix Daemon"
start on filesystem
stop on shutdown
respawn
env SSL_CERT_FILE=/nix/var/nix/profiles/default/etc/ssl/certs/ca-bundle.crt
exec /nix/var/nix/profiles/default/bin/nix-daemon $EXTRA_OPTS
EOF

	sudo chmod 644 /etc/init/nix-daemon.conf
	sudo initctl reload-configuration
	sudo service nix-daemon start

else
	echo "No initd system"
	exit 1
fi


echo "7. Nix multi user profile script"
cat <<'EOF' | sudo tee /etc/nix/nix-profile.sh
# From https://gist.github.com/benley/e4a91e8425993e7d6668

# Heavily cribbed from the equivalent NixOS login script.
# This should work better with multi-user nix setups.

export NIXPKGS_CONFIG="/etc/nix/nixpkgs-config.nix"
export NIX_OTHER_STORES="/run/nix/remote-stores/\*/nix"
export NIX_USER_PROFILE_DIR="/nix/var/nix/profiles/per-user/$USER"
export NIX_PROFILES="/nix/var/nix/profiles/default $HOME/.nix-profile"
export NIX_PATH="/nix/var/nix/profiles/per-user/root/channels"
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
  export NIX_PATH="nixpkgs=$HOME/.nix-defexpr/channels/nixpkgs${NIX_PATH:+:$NIX_PATH}"

  # Make sure nix-channel --update works
  SSL_CERT_FILE=/nix/var/nix/profiles/default/etc/ssl/certs/ca-bundle.crt
  CURL_CA_BUNDLE=$SSL_CERT_FILE
fi
EOF

echo "8. Set up the new default (root) profile"
update_nix
as_root "echo 'source /etc/nix/nix-profile.sh' >> /root/.bashrc"

echo "9. Set up the user profile"
sudo mkdir -p "/nix/var/nix/gcroots/per-user/$USER"
sudo chown -R "$USER":"$USER" "/nix/var/nix/profiles/per-user/$USER" "/nix/var/nix/gcroots/per-user/$USER"
rm -rf "$HOME/.nix-profile"
echo "source /etc/nix/nix-profile.sh" >> ~/.bashrc
source /etc/nix/nix-profile.sh
nix-channel --remove nixpkgs

echo "10. Installing git and gnumake as user"
nix-env -iA nixpkgs.git
nix-env -iA nixpkgs.gnumake

echo "All done !"
echo "Please open a new shell, or run: source /etc/nix/nix-profile.sh"
