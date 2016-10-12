.. _pre-requirement:

Pre-requirement
===============

To start working with ``mozilla-releng/services`` there is only one tools that
is required to be installed on your system: Nix_. Nix (package manager) works
alongside any other package manager and can be used with any Linux
distribution. Many developers confuse Nix_ (the package manager) with NixOS_
(Linux distribution).

Bellow instructions should work on any recent enough Linux distribution.

It is important to know that Nix_ can be safely uninstalled by removing
following folders:

.. code-block:: bash

    % sudo rm -rf /nix /etc/nix /home/$USER/.nix*


While installing Nix_ as in a *single user mode* is completly sufficient if you
want use Nix as packages manager. In case of ``mozilla-releng/services`` we
need to install Nix in *multi user mode* for build isolation reasons. This
means that builds will be perfomed in an isolated chroot environment and thus
giving us better *reproducablity* accross different machines.

All of the bellow steps could be done in one script, but for the purpose of
understanding what is happening during setup all steps are described in
details.


1. Installing Nix as single user mode
-------------------------------------

As ``$USER`` run:

.. code-block:: bash

    % sudo mkdir -m 0755 /nix
    % chown $USER /nix
    % curl https://nixos.org/nix/install | sh


2. Add custom binary cache
--------------------------

During our build process we also generate binaries which can be also used
locally to speed up building times locally.

.. code-block:: bash

    % mkdir -p /etc/nix
    % echo 'binary-caches = https://s3.amazonaws.com/releng-cache/ https://cache.nixos.org/' > /etc/nix/nix.conf


3. Add build group and users for multi user mode
------------------------------------------------

As ``root`` user run:

.. code-block:: bash

    % groupadd -r nixbld
    % for n in $(seq 1 10); do useradd -c "Nix build user $n" \
          -d /var/empty -g nixbld -G nixbld -M -N -r -s "$(which nologin)" \
          nixbld$n; done

And configure Nix to use above create group:

.. code-block:: bash

    % mkdir /etc/nix
    % echo "build-users-group = nixbld" >> /etc/nix/nix.conf


Give the nix store to ``root:nixbld`` ownership:

.. code-block:: bash

    % chown -R root:nixbld /nix
    % chmod 1777 /nix/var/nix/profiles/per-user
    % mkdir -m 1777 -p /nix/var/nix/gcroots/per-user


4. Migrating from single user to multi user mode
------------------------------------------------

Run as ``$USER``:

.. code-block:: bash

    % rm $HOME/.nix-profile
    % rm -r $HOME/.nix-defexpr
    % cp -r /nix/var/nix/profiles/default-*-link /nix/var/nix/profiles/per-user/$USER/profile-1-link

If default-\*-link doesn't exist it's safe to skip that stage. It's only
necessary to keep any software already installed using nix.

If there are multiple matches for default-\*-link then use the numerically
highest one.


5. Add ``nix-daemon`` systemd service
-------------------------------------

``nix-daemon`` serves as a service which schedules all the builds when
``nix-build`` or ``nix-shell`` command are invoked. Builds are run as
unpriviliged ``nixbld`` users which creates extra isolations (appart from
running in chroot).

.. code-block:: bash

    % cat <<"EOF" > /etc/systemd/system/nix-daemon.service
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

    % mkdir -p /nix/var/nix/daemon-socket
    % systemctl enable nix-daemon
    % systemctl start nix-daemon


6. Nix multi user profile script
--------------------------------

To hook Nix with create the following script (as ``root`` user):

.. code-block:: bash

    % cat <<"EOF" > /etc/nix/nix-profile.sh
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


7. Set up the new default (root) profile
----------------------------------------

As ``root`` user run:

.. code-block:: bash

    % source /etc/nix/nix-profile.sh
    % nix-channel --update
    % nix-env -p /nix/var/nix/profiles/default \
              -f /root/.nix-defexpr/channels/nixpkgs/ \
              -iA nix
    % nix-env -iA nixpkgs.nix nixpkgs.cacert

We must also ensure that at every shell login we run ``source
/etc/nix/nix-profile.sh``. This would usually mean running this command:

.. code-block:: bash

    % echo "source /etc/nix/nix-profile.sh" >> /root/.bashrc


8. Set up the user profile
--------------------------

As ``$USER`` run:

.. code-block:: bash

    % sudo chown $USER:$USER /nix/var/nix/profiles/per-user/$USER
    % echo "source /etc/nix/nix-profile.sh" >> ~/.bashrc
    % nix-channel --remove nixpkgs

Last command might vary depending which shell are you using.


9. Installing git and gnumake as user
-------------------------------------

As ``$USER`` run:

.. code-block:: bash

    % nix-env -iA nixpkgs.git
    % nix-env -iA nixpkgs.gnumake

Now ``git`` and ``make`` commands are in your ``$PATH``.


.. _Nix: https://nixos.org/nix
.. _NixOS: https://nixos.org
