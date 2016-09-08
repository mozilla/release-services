#/bin/bash

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
rm -f tmp/tc_cache_secrets
wget $TASKCLUSTER_SECRETS -o tmp/taskcluster_secrets

make build-tool-jq

export CACHE_BUCKET=`cat tmp/tc_cache_secrets | ./result-tool-jq/bin/jq -r '.secret.CACHE_BUCKET'`
export CACHE_AWS_ACCESS_KEY_ID=`cat tmp/tc_cache_secrets | ./result-tool-jq/bin/jq -r '.secret.CACHE_AWS_ACCESS_KEY_ID'`
export CACHE_AWS_SECRET_ACCESS_KEY=`cat tmp/tc_cache_secrets | ./result-tool-jq/bin/jq -r '.secret.CACHE_AWS_SECRET_ACCESS_KEY'`
export AWS_ACCESS_KEY_ID=`cat tmp/tc_cache_secrets | ./result-tool-jq/bin/jq -r '.secret.AWS_ACCESS_KEY_ID'`
export AWS_SECRET_ACCESS_KEY=`cat tmp/tc_cache_secrets | ./result-tool-jq/bin/jq -r '.secret.AWS_SECRET_ACCESS_KEY'`
export HEROKU_USERNAME=`cat tmp/tc_cache_secrets | ./result-tool-jq/bin/jq -r '.secret.HEROKU_USERNAME'`
export HEROKU_PASSWORD=`cat tmp/tc_cache_secrets | ./result-tool-jq/bin/jq -r '.secret.HEROKU_PASSWORD'`

make build-app

if [[ "$GITHUB_BASE_BRANCH" = "staging" ]] ||
   [[ "$GITHUB_BASE_BRANCH" = "production" ]]; then
    make deploy-$GITHUB_BASE_BRANCH-$APP
fi

make deploy-cache APP=$APP
