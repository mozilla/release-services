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
rm -f tmp/taskcluster_secrets
wget $TASKCLUSTER_SECRETS -O tmp/taskcluster_secrets

make build-tool-jq build-app APP=$APP

if [[ "$GITHUB_BASE_BRANCH" = "staging" ]] ||
   [[ "$GITHUB_BASE_BRANCH" = "production" ]]; then
    make deploy-$GITHUB_BASE_BRANCH-$APP \
        APP=$APP \
        AWS_ACCESS_KEY_ID=`cat tmp/taskcluster_secrets | ./result-tool-jq/bin/jq -r '.secret.AWS_ACCESS_KEY_ID'` \
        AWS_SECRET_ACCESS_KEY=`cat tmp/taskcluster_secrets | ./result-tool-jq/bin/jq -r '.secret.AWS_SECRET_ACCESS_KEY'` \
        HEROKU_USERNAME=`cat tmp/taskcluster_secrets | ./result-tool-jq/bin/jq -r '.secret.HEROKU_USERNAME'` \
        HEROKU_PASSWORD=`cat tmp/taskcluster_secrets | ./result-tool-jq/bin/jq -r '.secret.HEROKU_PASSWORD'`
fi

make deploy-cache \
    CACHE_BUCKET=`cat tmp/taskcluster_secrets | ./result-tool-jq/bin/jq -r '.secret.CACHE_BUCKET'` \
    AWS_ACCESS_KEY_ID=`cat tmp/taskcluster_secrets | ./result-tool-jq/bin/jq -r '.secret.CACHE_AWS_ACCESS_KEY_ID'` \
    AWS_SECRET_ACCESS_KEY=`cat tmp/taskcluster_secrets | ./result-tool-jq/bin/jq -r '.secret.CACHE_AWS_SECRET_ACCESS_KEY'`
