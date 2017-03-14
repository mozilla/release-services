FROM nixos/nix:1.11

ENV NIX_PATH="nixpkgs=https://github.com/NixOS/nixpkgs-channels/archive/fa4167c0a13cbe0d97b9c88d91b86845a8c4e740.tar.gz"

COPY nix/nix.conf /etc/nix/nix.conf
COPY .git/ /app/.git/
COPY lib/ /app/lib/
COPY nix/ /app/nix/
COPY src/ /app/src/
COPY VERSION /app/

RUN nix-channel --update
# TODO: remove downloaded packages
RUN nix-env -iA nixpkgs.nix nixpkgs.cacert nixpkgs.git nixpkgs.gnumake \
 && nix-collect-garbage -d

RUN cd /app && nix-shell nix/default.nix -A releng_frontend --run "exit"
RUN cd /app && nix-shell nix/default.nix -A releng_clobberer --run "exit"
RUN cd /app && nix-shell nix/default.nix -A releng_tooltool --run "exit"
RUN cd /app && nix-shell nix/default.nix -A releng_treestatus --run "exit"
RUN cd /app && nix-shell nix/default.nix -A releng_mapper --run "exit"
RUN cd /app && nix-shell nix/default.nix -A releng_archiver --run "exit"
RUN cd /app && nix-shell nix/default.nix -A shipit_bot_uplift --run "exit"
RUN cd /app && nix-shell nix/default.nix -A shipit_dashboard --run "exit"
RUN cd /app && nix-shell nix/default.nix -A shipit_frontend --run "exit"
RUN cd /app && nix-shell nix/default.nix -A shipit_pipeline --run "exit"
RUN cd /app && nix-shell nix/default.nix -A shipit_signoff --run "exit"

# Doing this after all the nix installation means rebuilds are faster for Makefile-only changes
COPY Makefile /app/

WORKDIR /app
ENTRYPOINT ["/root/.nix-profile/bin/make"]
CMD ["docker-run", "APP=${SERVICES_APP}"]
