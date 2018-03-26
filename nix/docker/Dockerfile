FROM debian:jessie-slim
MAINTAINER rgarbas@mozilla.com

ARG NIXPKGS_OWNER
ARG NIXPKGS_REPO
ARG NIXPKGS_REV
ARG NIXPKGS_SHA256
ARG NIX_VERSION
ARG NIX_SHA256
ARG NIX_CACHE_PUBLIC_KEYS
ARG NIX_CACHE_PUBLIC_URLS

ENV NIXPKGS_OWNER ${NIXPKGS_OWNER}
ENV NIXPKGS_REPO ${NIXPKGS_REPO}
ENV NIXPKGS_REV ${NIXPKGS_REV}
ENV NIXPKGS_SHA256 ${NIXPKGS_SHA256}
ENV NIX_VERSION ${NIX_VERSION}
ENV NIX_SHA256 ${NIX_SHA256}
ENV NIX_CACHE_PUBLIC_KEYS ${NIX_CACHE_PUBLIC_KEYS}
ENV NIX_CACHE_PUBLIC_URLS ${NIX_CACHE_PUBLIC_URLS}
ENV NIX_PATH "nixpkgs=/etc/nix/nixpkgs"

#
# install some package which are need from debian
#
RUN apt-get -q update \
 && apt-get -q --yes install bash wget bzip2 tar locales sudo \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
 && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
 && locale-gen \
 && sed -i "s|mesg n|tty -s && mesg n|" /root/.profile


#
# create app user and make sure it is paswordless sudo, that way we could start
# nix-daemon in the background when logging
#
RUN groupadd app \
 && useradd --create-home -g app -G sudo app \
 && sed -i -e "s|%sudo	ALL=(ALL:ALL) ALL|%sudo	ALL=(ALL) NOPASSWD: ALL|" /etc/sudoers


#
# Downloading nixpkgs
RUN wget -nv "https://github.com/$NIXPKGS_OWNER/$NIXPKGS_REPO/archive/$NIXPKGS_REV.tar.gz" \
 && nixpkgs_sha256=$(sha256sum "$NIXPKGS_REV.tar.gz" | cut -d' ' -f1) \
 && if [ "$nixpkgs_sha256" != "$NIXPKGS_SHA256" ]; then \
      echo "nixpkgs sha256 doesn't match. Expecting '$NIXPKGS_SHA256', but we got is '$nixpkgs_sha256'"; \
      exit 1; \
    fi \
 && tar zxf "$NIXPKGS_REV.tar.gz" \
 && mkdir /etc/services \
 && mkdir -p /etc/nix \
 && mv "$NIXPKGS_REPO-$NIXPKGS_REV" /etc/nix/nixpkgs


#
# Copy project into /app
#

#
# Install nix
RUN mkdir -m 0755 /nix \
 && chown app:app /nix \
 && mkdir -p /etc/nix \
 && echo "substituters = https://cache.nixos.org $NIX_CACHE_PUBLIC_URLS" >> /etc/nix/nix.conf \
 && echo "trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY= $NIX_CACHE_PUBLIC_KEYS" >> /etc/nix/nix.conf \
 # TODO: this is currently set to false once both cache bucket have only signed binaries we can set this to true
 && echo "require-sigs = false" >> /etc/nix/nix.conf \
 && echo "trusted-users = app" >> /etc/nix/nix.conf \
 && echo "allowed-users = app" >> /etc/nix/nix.conf \
 && echo "build-users-group =" >> /etc/nix/nix.conf


USER app
WORKDIR /home/app
ENV USER="app"

COPY please /app/
COPY VERSION /app/
COPY nix/ /app/nix/
COPY lib/ /app/lib/
COPY src/ /app/src/

RUN wget -nv "https://nixos.org/releases/nix/nix-$NIX_VERSION/nix-$NIX_VERSION-x86_64-linux.tar.bz2" \
 && nix_sha256=$(sha256sum "nix-$NIX_VERSION-x86_64-linux.tar.bz2" | cut -d' ' -f1) \
 && if [ "$nix_sha256" != "$NIX_SHA256" ]; then \
      echo "nix sha256 doesn't match. Expecting '$NIX_SHA256', but we got is '$nix_sha256'"; \
      exit 1; \
    fi \
 && tar jxf "nix-$NIX_VERSION-x86_64-linux.tar.bz2" \
 && sh ./nix-$NIX_VERSION-x86_64-linux/install \
 && . $HOME/.nix-profile/etc/profile.d/nix.sh \
 && rm -r $HOME/nix-*-x86_64-linux \
 && nix-collect-garbage -d \
 && rm -rf $HOME/.cache/nix \
 && nix-build /app/nix/default.nix -A please-cli -A tools --no-out-link


USER root


RUN chown -R root:root /nix \
 && chmod 1777 /nix/var/nix/profiles/per-user /nix/var/nix/gcroots/per-user \
 && rm -f /nix/var/nix/profiles/per-user/app/channels* \
 && mv /nix/var/nix/profiles/per-user/app/profile-1-link /nix/var/nix/profiles/default-1-link \
 && cd /nix/var/nix/profiles && ln -s default-1-link default && cd $HOME \
 && /nix/var/nix/profiles/default/bin/nix-env -iA bash -p /nix/var/nix/profiles/sandbox -f /etc/nix/nixpkgs \
 && /nix/var/nix/profiles/default/bin/nix-env -iA cacert -p /nix/var/nix/profiles/default -f /etc/nix/nixpkgs \
 && BASH_PATH=$(realpath /nix/var/nix/profiles/sandbox/bin/bash) \
 && BASH_DEPS=$(sudo "/nix/var/nix/profiles/default/bin/nix-store" -qR "$BASH_PATH" | tr '\n' ' ') \
 && echo "sandbox = true" >> /etc/nix/nix.conf \
 && echo "sandbox-paths = /bin/sh=$BASH_PATH $BASH_DEPS">> /etc/nix/nix.conf

COPY nix/docker/profile.sh /etc/nix/

RUN echo '. /etc/nix/profile.sh' >> $HOME/.bashrc \
 && mkdir -p /nix/var/nix/gcroots/per-user/app \
 && chown -R app:app /nix/var/nix/profiles/per-user/app /nix/var/nix/gcroots/per-user/app \
 && rm -rf $HOME/.nix-*

USER app
WORKDIR /app

RUN echo ". /etc/nix/profile.sh" >> $HOME/.bashrc \
 && rm -rf $HOME/.nix-*

COPY nix/docker/entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]

CMD /bin/bash
WORKDIR /app

#
# install please command
#
ENV GIT_SSL_CAINFO=/nix/var/nix/profiles/default/etc/ssl/certs/ca-bundle.crt
ENV NIX_SSL_CERT_FILE=/nix/var/nix/profiles/default/etc/ssl/certs/ca-bundle.crt
ENV LANG=en_US.UTF-8

