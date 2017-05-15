#!/bin/bash
set -e

nix-env -iA nixpkgs.gnumake nixpkgs.curl nixpkgs.cacert
export SSL_CERT_FILE="$HOME/.nix-profile/etc/ssl/certs/ca-bundle.crt"
mkdir -p /src 
cd /src 
curl -L "https://github.com/mozilla-releng/services/archive/${GITHUB_HEAD_SHA}.tar.gz" -o "${GITHUB_HEAD_SHA}.tar.gz"
tar zxf "${GITHUB_HEAD_SHA}.tar.gz"
cd "services-${GITHUB_HEAD_SHA}"


if [[ -z "$APP" ]] ||
   [[ -z "$TASKCLUSTER_SECRETS" ]]; then
  echo ""
  echo "You need to specify the following environment variables"
  echo "before running this sciprt:"
  echo "  export APP=\"releng_clobberer\"";
  echo "  export TASKCLUSTER_SECRETS=\"releng_clobberer\"";
  echo "";
  echo "";
  exit 1;
fi


mkdir -p /etc/nix
echo 'binary-caches = https://s3.amazonaws.com/releng-cache/ https://cache.nixos.org/' > /etc/nix/nix.conf

mkdir -p tmp
rm -f tmp/taskcluster_secrets
wget "$TASKCLUSTER_SECRETS" -O tmp/taskcluster_secrets

make build-pkgs-jq build-app APP="$APP"

if [[ "$GITHUB_BASE_BRANCH" = "staging" ]] ||
   [[ "$GITHUB_BASE_BRANCH" = "production" ]]; then
    make "deploy-${GITHUB_BASE_BRANCH}-${APP}" \
        APP="$APP" \
        AWS_ACCESS_KEY_ID="$(./result-pkgs-jq/bin/jq -r '.secret.AWS_ACCESS_KEY_ID' < tmp/taskcluster_secrets)" \
        AWS_SECRET_ACCESS_KEY="$(./result-pkgs-jq/bin/jq -r '.secret.AWS_SECRET_ACCESS_KEY' < tmp/taskcluster_secrets)" \
        HEROKU_USERNAME="$(./result-pkgs-jq/bin/jq -r '.secret.HEROKU_USERNAME' < tmp/taskcluster_secrets)" \
        HEROKU_PASSWORD="$(./result-pkgs-jq/bin/jq -r '.secret.HEROKU_PASSWORD' < tmp/taskcluster_secrets)"
fi

if [[ "$GITHUB_PULL_REQUEST" = "" ]]; then
    make taskcluster-hooks \
        APP="$APP" \
        BRANCH="$GITHUB_BASE_BRANCH" \
        HOOKS_URL="http://$(grep taskcluster /etc/hosts | awk '{ print $1 }')/hooks/v1" \
        DOCKER_USERNAME="$(./result-pkgs-jq/bin/jq -r '.secret.DOCKER_USERNAME' < tmp/taskcluster_secrets)" \
        DOCKER_PASSWORD="$(./result-pkgs-jq/bin/jq -r '.secret.DOCKER_PASSWORD' < tmp/taskcluster_secrets)"
fi

make deploy-cache \
    CACHE_BUCKET="$(./result-pkgs-jq/bin/jq -r '.secret.CACHE_BUCKET' < tmp/taskcluster_secrets)" \
    AWS_ACCESS_KEY_ID="$(./result-pkgs-jq/bin/jq -r '.secret.AWS_ACCESS_KEY_ID' < tmp/taskcluster_secrets)" \
    AWS_SECRET_ACCESS_KEY="$(./result-pkgs-jq/bin/jq -r '.secret.AWS_SECRET_ACCESS_KEY' < tmp/taskcluster_secrets)"

echo "Success!"
