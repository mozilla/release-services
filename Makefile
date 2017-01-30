ifneq ($(shell uname), Linux)
$(error Only Linux is supported now. PRs are welcome!)
endif

.PHONY: *

APP=
APPS=\
	elm_common_example \
	releng_docs \
	releng_clobberer \
	releng_tooltool \
	releng_treestatus \
	releng_mapper \
	releng_archiver \
	releng_frontend \
	shipit_dashboard \
	shipit_bot_uplift \
	shipit_pipeline \
	shipit_signoff \
	shipit_frontend

TOOL=
TOOLS=\
	awscli \
	coreutils \
	createcert \
	gnused \
	jq \
	mysql2pgsql \
	mysql2sqlite \
	node2nix \
	push \
	pypi2nix \
	taskcluster-hooks
VERSION=$(shell cat VERSION)

APP_DEV_DBNAME=services

APP_DEV_HOST=localhost

APP_DEV_PORT_releng_docs=7000
APP_DEV_PORT_elm_common_example=7001

APP_DEV_PORT_releng_frontend=8000
APP_DEV_PORT_releng_clobberer=8001
APP_DEV_PORT_releng_tooltool=8002
APP_DEV_PORT_releng_treestatus=8003
APP_DEV_PORT_releng_mapper=8004
APP_DEV_PORT_releng_archiver=8005

APP_DEV_PORT_shipit_frontend=8010
APP_DEV_PORT_shipit_dashboard=8011
APP_DEV_PORT_shipit_pipeline=8012
APP_DEV_PORT_shipit_signoff=8013

APP_DEV_POSTGRES_PORT=9000

APP_DEV=\
	NEO_VERSION='v$(VERSION) (devel)' \
	NEO_DOCS_URL='http://$(APP_DEV_HOST):$(APP_DEV_PORT_releng_docs)' \
	SSL_CACERT=$$PWD/tmp/ca.crt \
	SSL_CERT=$$PWD/tmp/server.crt \
	SSL_KEY=$$PWD/tmp/server.key
APP_DEV_ENV_elm_common_example=\
	$(APP_DEV)
APP_DEV_ENV_releng_frontend=\
	NEO_DOCS_URL=https://$(APP_DEV_HOST):$(APP_DEV_PORT_releng_docs) \
	NEO_CLOBBERER_URL=https://$(APP_DEV_HOST):$(APP_DEV_PORT_releng_clobberer) \
	NEO_TOOLTOOL_URL=https://$(APP_DEV_HOST):$(APP_DEV_PORT_releng_tooltool) \
	NEO_TREESTATUS_URL=https://$(APP_DEV_HOST):$(APP_DEV_PORT_releng_treestatus) \
	NEO_MAPPER_URL=https://$(APP_DEV_HOST):$(APP_DEV_PORT_releng_mapper) \
	NEO_ARCHIVER_URL=https://$(APP_DEV_HOST):$(APP_DEV_PORT_releng_archiver) \
	$(APP_DEV)
APP_DEV_ENV_shipit_frontend=\
	NEO_DASHBOARD_URL=https://$(APP_DEV_HOST):$(APP_DEV_PORT_shipit_dashboard) \
	NEO_PIPELINE_URL=https://$(APP_DEV_HOST):$(APP_DEV_PORT_shipit_pipeline) \
	NEO_BUGZILLA_URL=https://bugzilla-dev.allizom.org \
	$(APP_DEV)

APP_STAGING_HEROKU_releng_clobberer=releng-staging-clobberer
APP_STAGING_HEROKU_releng_tooltool=releng-staging-tooltool
APP_STAGING_HEROKU_releng_treestatus=releng-staging-treestatus
APP_STAGING_HEROKU_releng_mapper=releng-staging-mapper
APP_STAGING_HEROKU_releng_archiver=releng-staging-archiver

APP_STAGING_HEROKU_shipit_dashboard=shipit-staging-dashboard

APP_STAGING_S3_releng_docs=releng-staging-docs
APP_STAGING_S3_releng_frontend=releng-staging-frontend
APP_STAGING_S3_shipit_frontend=shipit-staging-frontend
APP_STAGING_CSP_releng_frontend=https://auth.taskcluster.net https://clobberer.staging.mozilla-releng.net https://tooltool.staging.mozilla-releng.net https://treestatus.staging.mozilla-releng.net https://mapper.staging.mozilla-releng.net https://archiver.staging.mozilla-releng.net
APP_STAGING_ENV_releng_frontend=\
	'version="v$(VERSION)"' \
	'docs-url="https:\/\/docs\.staging\.mozilla-releng\.net\"' \
	'clobberer-url="https:\/\/clobberer\.staging\.mozilla-releng\.net\"' \
	'tooltool-url="https:\/\/tooltool\.staging\.mozilla-releng\.net\"' \
	'treestatus-url="https:\/\/treestatus\.staging\.mozilla-releng\.net\"' \
	'mapper-url="https:\/\/mapper\.staging\.mozilla-releng\.net\"' \
	'archiver-url="https:\/\/archiver\.staging\.mozilla-releng\.net\"'
APP_STAGING_CSP_shipit_frontend=https://auth.taskcluster.net https://dashboard.shipit.staging.mozilla-releng.net https://bugzilla.mozilla.org
APP_STAGING_ENV_shipit_frontend=\
	'version="v$(VERSION)"' \
	'dashboard-url="https:\/\/dashboard\.shipit\.staging\.mozilla-releng\.net\"' \
	'bugzilla-url="https:\/\/bugzilla\.mozilla\.org"'

APP_PRODUCTION_HEROKU_releng_clobberer=releng-production-clobberer
APP_PRODUCTION_HEROKU_releng_tooltool=releng-production-tooltool
APP_PRODUCTION_HEROKU_releng_treestatus=releng-production-treestatus
APP_PRODUCTION_HEROKU_releng_mapper=releng-production-mapper
APP_PRODUCTION_HEROKU_releng_archiver=releng-production-archiver
APP_PRODUCTION_HEROKU_shipit_dashboard=shipit-production-dashboard

APP_PRODUCTION_S3_releng_docs=releng-production-docs
APP_PRODUCTION_S3_releng_frontend=releng-production-frontend
APP_PRODUCTION_S3_shipit_frontend=shipit-production-frontend
APP_PRODUCTION_CSP_releng_frontend=https://auth.taskcluster.net https://clobberer.mozilla-releng.net https://tooltool.mozilla-releng.net https://treestatus.mozilla-releng.net https://mapper.mozilla-releng.net https://archiver.mozilla-releng.net
APP_PRODUCTION_ENV_releng_frontend=\
	'version="v$(VERSION)"' \
	'docs-url="https:\/\/docs\.mozilla-releng\.net\"' \
	'clobberer-url="https:\/\/clobberer\.mozilla-releng\.net\"' \
	'tooltool-url="https:\/\/tooltool\.mozilla-releng\.net\"' \
	'treestatus-url="https:\/\/treestatus\.mozilla-releng\.net\"' \
	'mapper-url="https:\/\/mapper\.mozilla-releng\.net\"' \
	'archiver-url="https:\/\/archiver\.mozilla-releng\.net\"'
APP_PRODUCTION_CSP_shipit_frontend=https://auth.taskcluster.net https://dashboard.shipit.mozilla-releng.net https://bugzilla.mozilla.org
APP_PRODUCTION_ENV_shipit_frontend=\
	'version="$(VERSION)"' \
	'dashboard-url="https:\/\/dashboard\.shipit\.mozilla-releng\.net\"'

FLASK_CMD ?= shell # default value for flask command to run


help:
	@echo ""
	@echo "To enter a shell to develop application do:"
	@echo "  $$ make develop APP=<application>"
	@echo ""
	@echo "To run a developing application do:"
	@echo "  $$ make develop-run APP=<application>"
	@echo ""
	@echo "To run tests for specific application do:"
	@echo "  $$ make build-app APP=<application>"
	@echo ""
	@if [ -z "$(APP)" ]; then \
		echo "Available APPs are: "; \
		for app in $(APPS); do \
			echo " - $$app"; \
		done; \
		echo ""; \
	fi
	@echo ""
	@echo "For more information look at: https://docs.mozilla-releng.net"


nix:
	@if [ -z "`which nix-build`" ]; then \
		echo ""; \
		echo "This Makefile uses Nix packages to run commands in an isolated environment."; \
		echo ""; \
		echo "To install Nix please follow instructions on https://nixos.org/nix/"; \
		echo ""; \
		echo "For inpatients, run the following curl-bash"; \
		echo ""; \
		echo "$$ curl https://nixos.org/nix/install | sh; . \$$HOME/.nix-profile/etc/profile.d/nix.sh"; \
		echo ""; \
		echo "and rerun the same command again"; \
		echo ""; \
		exit 1; \
	fi


develop: nix require-APP
	@SSL_DEV_CA=$$PWD/tmp nix-shell nix/default.nix -A $(APP)




develop-run: require-APP develop-run-$(APP)

develop-run-SPHINX : nix require-APP
	nix-shell nix/default.nix -A releng_docs --run "HOST=$(APP_DEV_HOST) PORT=$(APP_DEV_PORT_$(APP)) python run.py"

develop-run-BACKEND: build-certs nix require-APP
	DEBUG=true \
	CACHE_TYPE=filesystem \
	CACHE_DIR=$$PWD/src/$(APP)/cache \
	APP_SETTINGS=$$PWD/src/$(APP)/settings.py \
	CORS_ORIGINS="*" \
		nix-shell nix/default.nix -A $(APP) \
		--run "gunicorn $(APP):app --bind '$(APP_DEV_HOST):$(APP_DEV_PORT_$(APP))' --ca-certs=$$PWD/tmp/ca.crt --certfile=$$PWD/tmp/server.crt --keyfile=$$PWD/tmp/server.key --workers 1 --timeout 3600 --reload --log-file -"

develop-run-FRONTEND: build-certs nix require-APP
	nix-shell nix/default.nix --pure -A $(APP) \
		--run "$(APP_DEV_ENV_$(APP)) neo start --port $(APP_DEV_PORT_$(APP)) --config webpack.config.js"

develop-run-releng_docs: develop-run-SPHINX
develop-run-elm_common_example: develop-run-FRONTEND

develop-run-releng_frontend: develop-run-FRONTEND
develop-run-releng_clobberer: require-sqlite develop-run-BACKEND
develop-run-releng_tooltool: require-sqlite develop-run-BACKEND
develop-run-releng_treestatus: require-postgres develop-run-BACKEND
develop-run-releng_mapper: require-sqlite develop-run-BACKEND
develop-run-releng_archiver: require-sqlite develop-run-BACKEND

develop-run-shipit_frontend: develop-run-FRONTEND
develop-run-shipit_dashboard: require-postgres develop-run-BACKEND
develop-run-shipit_pipeline: require-sqlite develop-run-BACKEND
develop-run-shipit_signoff: require-sqlite develop-run-BACKEND

develop-run-postgres: build-postgresql require-initdb
	./result-tool-postgresql/bin/postgres -D $(PWD)/tmp/postgres -h localhost -p $(APP_DEV_POSTGRES_PORT)

develop-flask-shell: nix require-APP
	DEBUG=true \
	CACHE_TYPE=filesystem \
	CACHE_DIR=$$PWD/src/$(APP)/cache \
	FLASK_APP=$(APP) \
	APP_SETTINGS=$$PWD/src/$(APP)/settings.py \
		nix-shell nix/default.nix -A $(APP) \
		--run "flask $(FLASK_CMD)"

build-apps: $(foreach app, $(APPS), build-app-$(app))

build-app: require-APP build-app-$(APP)

build-app-%: nix
	@nix-build nix/default.nix -A $(subst build-app-,,$@) -o result-$(subst build-app-,,$@) --fallback


build-docker: require-APP build-docker-$(APP)

build-docker-%: nix
	@nix-build nix/docker.nix -A $(subst build-docker-,,$@) -o result-docker-$(subst build-docker-,,$@) --fallback



deploy-staging-all: $(foreach app, $(APPS), deploy-staging-$(app))

deploy-staging: require-APP deploy-staging-$(APP)

deploy-staging-HEROKU: require-APP require-HEROKU build-tool-push build-docker-$(APP)
	./result-tool-push/bin/push \
		`realpath ./result-docker-$(APP)` \
		https://registry.heroku.com \
		-u $(HEROKU_USERNAME) \
		-p $(HEROKU_PASSWORD) \
		-N $(APP_STAGING_HEROKU_$(APP))/web \
		-T latest

deploy-staging-S3: \
			require-AWS \
			require-APP \
			build-tool-coreutils \
			build-tool-gnused \
			build-tool-awscli \
			build-app-$(APP)
	$(eval APP_TMP := $(shell ./result-tool-coreutils/bin/mktemp -d --tmpdir=$$PWD/tmp $(APP).XXXXX))
	./result-tool-coreutils/bin/cp -rf result-$(APP)/* $(APP_TMP)
	./result-tool-gnused/bin/sed -i "s|font-src 'self';|font-src 'self'; connect-src $(APP_STAGING_CSP_$(APP));|" $(APP_TMP)/index.html
	@for v in $(APP_STAGING_ENV_$(APP)) ; do \
		./result-tool-gnused/bin/sed -i "s|<body|<body data-$$v|" $(APP_TMP)/index.html ; \
	done
	./result-tool-awscli/bin/aws s3 sync \
		--delete \
		--acl public-read  \
		$(APP_TMP) \
		s3://$(APP_STAGING_S3_$(APP))

deploy-staging-elm_common_example:     # no deployment

deploy-staging-releng_frontend:        deploy-staging-S3
deploy-staging-releng_docs:            deploy-staging-S3
deploy-staging-releng_clobberer:       deploy-staging-HEROKU
deploy-staging-releng_tooltool:        deploy-staging-HEROKU
deploy-staging-releng_treestatus:      deploy-staging-HEROKU
deploy-staging-releng_mapper:          deploy-staging-HEROKU
deploy-staging-releng_archiver:        deploy-staging-HEROKU

deploy-staging-shipit_frontend:        deploy-staging-S3
deploy-staging-shipit_dashboard:       deploy-staging-HEROKU
deploy-staging-shipit_pipeline:        # deploy-staging-HEROKU
deploy-staging-shipit_signoff:         # deploy-staging-HEROKU




deploy-production-all: $(foreach app, $(APPS), deploy-production-$(app))

deploy-production: require-APP deploy-production-$(APP)

deploy-production-HEROKU: require-APP require-HEROKU build-tool-push build-docker-$(APP)
	./result-tool-push/bin/push \
		`realpath ./result-docker-$(APP)` \
		https://registry.heroku.com \
		-u $(HEROKU_USERNAME) \
		-p $(HEROKU_PASSWORD) \
		-N $(APP_PRODUCTION_HEROKU_$(APP))/web \
		-T latest

deploy-production-S3: \
			require-AWS \
			require-APP \
			build-tool-coreutils \
			build-tool-gnused \
			build-tool-awscli \
			build-app-$(APP)
	$(eval APP_TMP := $(shell ./result-tool-coreutils/bin/mktemp -d --tmpdir=$$PWD/tmp $(APP).XXXXX))
	./result-tool-coreutils/bin/cp -rf result-$(APP)/* $(APP_TMP)
	./result-tool-gnused/bin/sed -i "s|font-src 'self';|font-src 'self'; connect-src $(APP_PRODUCTION_CSP_$(APP));|" $(APP_TMP)/index.html
	@for v in $(APP_PRODUCTION_ENV_$(APP)) ; do \
		./result-tool-gnused/bin/sed -i "s|<body|<body data-$$v|" $(APP_TMP)/index.html ; \
	done
	./result-tool-awscli/bin/aws s3 sync \
		--delete \
		--acl public-read  \
		$(APP_TMP) \
		s3://$(APP_PRODUCTION_S3_$(APP))

deploy-production-elm_common_example:  # no deployment

deploy-production-releng_frontend:     deploy-production-S3
deploy-production-releng_docs:         deploy-production-S3
deploy-production-releng_clobberer:    # deploy-production-HEROKU
deploy-production-releng_tooltool:     # deploy-production-HEROKU
deploy-production-releng_treestatus:   deploy-production-HEROKU
deploy-production-releng_mapper:       # deploy-production-HEROKU
deploy-production-releng_archiver:     # deploy-production-HEROKU

deploy-production-shipit_frontend:     deploy-production-S3
deploy-production-shipit_dashboard:    deploy-production-HEROKU
deploy-production-shipit_pipeline:     # deploy-staging-HEROKU
deploy-production-shipit_signoff:      # deploy-staging-HEROKU



update-all: update-tools update-apps
update-tools: $(foreach tool, $(TOOLS), update-tool-$(tool))
update-apps: $(foreach app, $(APPS), update-app-$(app))

update-app: require-APP update-app-$(APP)
update-app-%: tmpdir nix
	nix-shell nix/update.nix --argstr pkg $(subst update-app-,,$@)


update-tool: require-TOOL update-tool-$(TOOL)
update-tool-%: tmpdir nix
	nix-shell nix/update.nix --argstr pkg tools.$(subst update-tool-,,$@)




build-tools: $(foreach tool, $(TOOLS), build-tool-$(tool))

build-tool: require-TOOL build-tool-$(TOOL)

build-tool-%: nix
	@nix-build nix/default.nix -A tools.$(subst build-tool-,,$@) -o result-tool-$(subst build-tool-,,$@) --fallback

build-postgresql: nix
	@nix-build nix/default.nix -A postgresql -o result-tool-postgresql --fallback


build-certs: tmpdir build-tool-createcert
	@if [ ! -e "$$PWD/tmp/ca.crt" ] && \
	   [ ! -e "$$PWD/tmp/ca.key" ] && \
	   [ ! -e "$$PWD/tmp/ca.srl" ] && \
	   [ ! -e "$$PWD/tmp/server.crt" ] && \
	   [ ! -e "$$PWD/tmp/server.key" ]; then \
	  ./result-tool-createcert/bin/createcert $$PWD/tmp; \
	fi



build-cache: tmpdir
	mkdir -p tmp/cache
	nix-push --dest "$$PWD/tmp/cache" --force ./result-*

deploy-cache: require-AWS require-CACHE_BUCKET build-tool-awscli build-cache
	./result-tool-awscli/bin/aws s3 sync \
		--size-only \
		--acl public-read  \
		tmp/cache/ \
		s3://$(CACHE_BUCKET)


taskcluster.yml: nix
	@nix-build nix/taskcluster.nix -o result-taskcluster --fallback
	@cp -f ./result-taskcluster .taskcluster.yml


taskcluster-hooks.json: require-APP require-BRANCH nix
	@nix-build nix/taskcluster_hooks.nix \
		--argstr app "$(APP)" \
		--argstr branch "$(BRANCH)" \
		-o result-taskcluster-hooks.json --fallback

taskcluster-hooks: taskcluster-hooks.json require-APP require-BRANCH require-DOCKER require-HOOKS_URL build-tool-push build-tool-taskcluster-hooks
	@./result-tool-taskcluster-hooks/bin/taskcluster-hooks \
		--hooks=./result-taskcluster-hooks.json \
        --hooks-group=project-releng \
        --hooks-prefix=services-$(BRANCH)-$(APP)- \
        --hooks-url=$(HOOKS_URL) \
        --docker-push=./result-tool-push/bin/push \
		--docker-registry=https://index.docker.io \
        --docker-repo=garbas/releng-services \
        --docker-username=$(DOCKER_USERNAME) \
        --docker-password=$(DOCKER_PASSWORD)

taskcluster-hooks-manual: taskcluster-hooks.json require-APP require-BRANCH require-DOCKER require-HOOKS_CREDS build-tool-push build-tool-taskcluster-hooks
	@./result-tool-taskcluster-hooks/bin/taskcluster-hooks \
		--hooks=./result-taskcluster-hooks.json \
        --hooks-group=project-releng \
        --hooks-prefix=services-$(BRANCH)-$(APP)- \
        --hooks-client-id=$(HOOKS_CLIENT_ID) \
        --hooks-access-token=$(HOOKS_ACCESS_TOKEN) \
        --docker-push=./result-tool-push/bin/push \
		--docker-registry=https://index.docker.io \
        --docker-repo=garbas/releng-services \
        --docker-username=$(DOCKER_USERNAME) \
        --docker-password=$(DOCKER_PASSWORD)



# --- helpers


tmpdir:
	@mkdir -p $$PWD/tmp


require-TOOL:
	@if [ -z "$(TOOL)" ]; then \
		echo ""; \
		echo "You need to specify which TOOL to build, eg:"; \
		echo "  make build-tool TOOL=awscli"; \
		echo "  ..."; \
		echo ""; \
		echo "Available TOOLS are: "; \
		for tool in $(TOOLS); do \
			echo " - $$tool"; \
		done; \
		echo ""; \
		exit 1; \
	fi

require-APP:
	@if [ -z "$(APP)" ]; then \
		echo ""; \
		echo "You need to specify which APP, eg:"; \
		echo "  make develop APP=releng_clobberer"; \
		echo "  make build-app APP=releng_clobberer"; \
		echo "  ..."; \
		echo ""; \
		echo "Available APPS are: "; \
		for app in $(APPS); do \
			echo " - $$app"; \
		done; \
		echo ""; \
		exit 1; \
	fi


require-AWS:
	@if [ -z "$$AWS_ACCESS_KEY_ID" ] || \
		[ -z "$$AWS_SECRET_ACCESS_KEY" ]; then \
		echo ""; \
		echo "You need to specify AWS credentials, eg:"; \
		echo "  make deploy-production-releng_frontend \\"; \
	    echo "       AWS_ACCESS_KEY_ID=\"...\" \\"; \
		echo "       AWS_SECRET_ACCESS_KEY=\"...\""; \
		echo ""; \
		echo ""; \
		exit 1; \
	fi

require-HEROKU:
	@if [ -z "$$HEROKU_USERNAME" ] || \
		[ -z "$$HEROKU_PASSWORD" ]; then \
		echo ""; \
		echo "You need to specify HEROKU credentials, eg:"; \
		echo "  make deploy-production-releng_clobberer \\"; \
	    echo "       HEROKU_USERNAME=\"...\" \\"; \
		echo "       HEROKU_PASSWORD=\"...\""; \
		echo ""; \
		echo ""; \
		exit 1; \
	fi

require-CACHE_BUCKET:
	@if [ -z "$$CACHE_BUCKET" ]; then \
		echo ""; \
		echo "You need to specify CACHE_BUCKET variable, eg:"; \
		echo "  make deploy-cache \\"; \
		echo "       CACHE_BUCKET=\"...\" \\"; \
		echo ""; \
		echo ""; \
		exit 1; \
	fi

require-DOCKER:
	@if [ -z "$(DOCKER_USERNAME)" ] || \
	    [ -z "$(DOCKER_PASSWORD)" ]; then \
		echo ""; \
		echo "You need to specify DOCKER_USERNAME and DOCKER_PASSWORD."; \
		echo ""; \
		echo ""; \
		exit 1; \
	fi

require-HOOKS_CREDS:
	@if [[ -z "$(HOOKS_CLIENT_ID)" ]] || \
	    [[ -z "$(HOOKS_ACCESS_TOKEN)" ]]; then \
		echo ""; \
		echo "You need to specify HOOKS_CLIENT_ID and HOOKS_ACCESS_TOKEN."; \
		echo ""; \
		echo ""; \
		exit 1; \
	fi

require-HOOKS_URL:
	@if [[ -z "$(HOOKS_URL)" ]]; then \
		echo ""; \
		echo "You need to specify HOOKS_URL."; \
		echo ""; \
		echo ""; \
		exit 1; \
	fi


require-BRANCH:
	@if [[ -z "$(BRANCH)" ]]; then \
		echo ""; \
		echo "You need to specify BRANCH."; \
		echo ""; \
		echo ""; \
		exit 1; \
	fi

require-initdb: build-postgresql
	$(eval PG_DATA := $(PWD)/tmp/postgres)
	@if [ ! -d $(PG_DATA) ]; then \
		./result-tool-postgresql/bin/initdb -D $(PG_DATA) --auth=trust; \
	fi

require-postgres: build-postgresql
	if [ "`./result-tool-postgresql/bin/psql -lqt -p $(APP_DEV_POSTGRES_PORT) | cut -d \| -f 1 | grep $(APP_DEV_DBNAME)| wc -l`" != "1" ]; then \
		./result-tool-postgresql/bin/createdb -p $(APP_DEV_POSTGRES_PORT) $(APP_DEV_DBNAME); \
	fi
	$(eval export DATABASE_URL=postgresql://localhost:$(APP_DEV_POSTGRES_PORT)/services)
	@echo "Using postgresql dev database $(DATABASE_URL)"

require-sqlite:
	$(eval export DATABASE_URL=sqlite:///$(PWD)/app.db)
	@echo "Using sqlite dev database $(DATABASE_URL)"



all: build-apps build-tools
