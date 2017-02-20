.. _prerequirements:

Prerequirements
===============

To start working with ``mozilla-releng/services`` there is only one tool that
is required to be installed on your system: Nix_. Nix (package manager) works
alongside any other package manager and can be used with any Linux
distribution.

It is important to know that Nix_ can be safely uninstalled by removing
following folders:

.. code-block:: bash

    % sudo rm -rf /nix /etc/nix /home/$USER/.nix*

Many developers confuse Nix_ (the package manager) with NixOS_ (Linux
distribution). In this case we will *only* install Nix, the package manager.

Bellow instructions should work on any recent enough Linux distribution
(we only tested below setup with latest distributions).

A fully automated script is available on the `Github Repository`_. It has been
succesfully tested on a fresh install of Ubuntu 16.04, and simply does the
following steps (except LVM optional setup just below)

.. _`Github Repository`: https://raw.githubusercontent.com/mozilla-releng/services/master/nix/setup.sh

0. Optional - Use LVM for Nix
-----------------------------

If you already use LVM on your Linux computer, you can create a separate Logical Volume just for the nix installation:

.. code-block:: bash

    % VG_NAME=$(vgdisplay | grep "VG Name" | awk '{print $3}')
    % lvcreate -L 15G -n nix $VG_NAME
    % mkfs.ext4 /dev/$VG_NAME/nix
    % mkdir /nix
    % echo "/dev/mapper/$VG_NAME/nix  /nix  ext4    defaults,noatime        0       2" >> /etc/fstab
    % mount -a


1. Installing Nix as single user mode
-------------------------------------

As ``$USER`` run:

.. code-block:: bash

    % sudo mkdir -m 0755 /nix
    % sudo chown $USER /nix
    % curl https://nixos.org/nix/install | sh

Above script will install Nix_ undex ``/nix`` and add ``~/.nix-profile/bin`` to
your ``$PATH``. You need to relogin to your terminal to be able to use
``nix-*`` commands.


2. Add custom binary cache
--------------------------

During our build process we also generate binaries which can be also used
locally to speed up building times locally.

As ``root`` user run:

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

    % echo "build-users-group = nixbld" >> /etc/nix/nix.conf

Give the nix store to ``root:nixbld`` ownership:

.. code-block:: bash

    % chown -R root:nixbld /nix
    % chmod 1777 /nix/var/nix/profiles/per-user
    % mkdir -m 1777 -p /nix/var/nix/gcroots/per-user


4. Enabling sandbox mode
------------------------

Builds will be performed in a sandboxed environment, i.e., they’re isolated
from the normal file system hierarchy and will only see their dependencies in
the Nix store, the temporary build directory, private versions of ``/proc``,
``/dev``, ``/dev/shm`` and ``/dev/pts`` (on Linux), and the paths configured
with the ``build-sandbox-paths`` option. This is useful to prevent undeclared
dependencies on files in directories such as ``/usr/bin``. In addition, on
Linux, builds run in private PID, mount, network, IPC and UTS namespaces to
isolate them from other processes in the system (except that fixed-output
derivations do not run in private network namespace to ensure they can access
the network).

As ``$USER`` run:

.. code-block:: bash

    % sudo echo "build-use-sandbox = true" >> /etc/nix/nix.conf
    % sudo mkdir -p /nix/var/nix/profiles
    % sudo /home/$USER/.nix-profile/bin/nix-env -iA nixpkgs.bash -p /nix/var/nix/profiles/sandbox
    % sudo echo "build-sandbox-paths = /bin/sh=`realpath /nix/var/nix/profiles/sandbox/bin/bash` `nix-store -qR \`realpath /nix/var/nix/profiles/sandbox/bin/bash\` | tr '\n' ' '`" >> /etc/nix/nix.conf


5. Migrating from single user to multi user mode
------------------------------------------------

Run as ``$USER``:

.. code-block:: bash

    % rm $HOME/.nix-profile
    % rm -r $HOME/.nix-defexpr
    % sudo cp -r /nix/var/nix/profiles/default-*-link /nix/var/nix/profiles/per-user/$USER/profile-1-link

If default-\*-link doesn't exist it's safe to skip that stage. It's only
necessary to keep any software already installed using nix.

If there are multiple matches for default-\*-link then use the numerically
highest one.


6. Add ``nix-daemon`` service
-----------------------------

``nix-daemon`` serves as a service which schedules all the builds when
``nix-build`` or ``nix-shell`` command are invoked. Builds are run as
unpriviliged ``nixbld`` users which creates extra isolations (appart from
running in chroot).

For systemd:

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

For upstart:

.. code-block:: bash

    % cat <<"EOF" > /etc/init/nix-daemon.conf
    description "Nix Daemon"
    start on filesystem
    stop on shutdown
    respawn
    env SSL_CERT_FILE=/nix/var/nix/profiles/default/etc/ssl/certs/ca-bundle.crt
    exec /nix/var/nix/profiles/default/bin/nix-daemon $EXTRA_OPTS
    EOF
    % chmod 644 /etc/init/nix-daemon.conf
    % initctl reload-configuration
    % service nix-daemon start


7. Nix multi user profile script


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


8. Set up the new default (root) profile
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


9. Set up the user profile
--------------------------

As ``$USER`` run:

.. code-block:: bash

    % sudo mkdir /nix/var/nix/gcroots/per-user/$USER
    % sudo chown -R $USER:$USER /nix/var/nix/profiles/per-user/$USER /nix/var/nix/gcroots/per-user/$USER
    % echo "source /etc/nix/nix-profile.sh" >> ~/.bashrc
    % nix-channel --remove nixpkgs

Last command might vary depending which shell are you using.


10. Installing git and gnumake as user
--------------------------------------

As ``$USER`` run:

.. code-block:: bash

    % nix-env -iA nixpkgs.git
    % nix-env -iA nixpkgs.gnumake

Now ``git`` and ``make`` commands are in your ``$PATH``.


.. _Nix: https://nixos.org/nix
.. _NixOS: https://nixos.org
