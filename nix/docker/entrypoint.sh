#!/bin/sh

if ! pgrep -x 'nix-daemon' ; then
    echo "Starting nix-daemon in the background (as root)..."
    sudo -i nix-daemon &>> $HOME/nix-daemon.log &
fi
exec "$@"
