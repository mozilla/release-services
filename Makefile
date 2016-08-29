.PHONY: *

APP=
APPS=\
	releng_frontend \
	releng_clobberer \
	shipit_dashboard

TOOL=
TOOLS=\
	pypi2nix \
	awscli \
	node2nix \
	mysql2sqlite \
	mysql2pgsql


APP_PORT_releng_frontend=8001
APP_PORT_releng_clobberer=8002
APP_PORT_shipit_frontend=8003
APP_PORT_shipit_dashboard=8004


help:
	@echo "TODO: need to write help for commands"


nix:
	@if [[ -z "`which nix-build`" ]]; then \
		curl https://nixos.org/nix/install | sh; \
		source $HOME/.nix-profile/etc/profile.d/nix.sh; \
	fi


develop: nix require-APP
	nix-shell nix/default.nix -A $(APP) --run $$SHELL




develop-run: require-APP develop-run-$(APP)

develop-run-BACKEND: nix require-APP 
	DEBUG=true \
	CACHE_TYPE=filesystem \
	CACHE_DIR=$$PWD/src/$(APP)/cache \
	DATABASE_URL=sqlite:///$$PWD/app.db \
	APP_SETTINGS=$$PWD/src/$(APP)/settings.py \
		nix-shell nix/default.nix -A $(APP) \
		--run "gunicorn $(APP):app --bind 'localhost:$(APP_PORT_$(APP))' --certfile=nix/dev_ssl/server.crt --keyfile=nix/dev_ssl/server.key --workers 2 --timeout 3600 --reload --log-file -"

develop-run-FRONTEND: nix require-APP 
	NEO_BASE_URL=https://localhost:$$APP_PORT_$(APP) \
		nix-shell nix/default.nix -A $(APP) --run "neo start --config webpack.config.js"

develop-run-releng_clobberer: develop-run-BACKEND
develop-run-releng_frontend: develop-run-FRONTEND

develop-run-shipit_dashboard: develop-run-BACKEND
develop-run-shipit_frontend: develop-run-BACKEND






build-apps: $(foreach app, $(APPS), build-app-$(app))

build-app: require-APP build-app-$(APP)

build-app-%: nix
	nix-build nix/default.nix -A $(subst build-app-,,$@) -o result-$(subst build-app-,,$@)



docker: require-APP docker-$(APP)

docker-%: nix
	rm -f result-$@
	nix-build nix/docker.nix -A $(subst docker-,,$@) -o result-$@



deploy-staging-all: $(foreach app, $(APPS), deploy-staging-$(app)) deploy-staging-docs

deploy-staging: require-APP deploy-staging-$(APP)

deploy-staging-releng_clobberer: docker-releng_clobberer
	if [[ -n "`docker images -q $(subst deploy-staging-,,$@)`" ]]; then \
		docker rmi -f `docker images -q $(subst deploy-staging-,,$@)`; \
	fi
	cat result-$(subst deploy-staging-,docker-,$@) | docker load
	docker tag `docker images -q \
		$(subst deploy-staging-,,$@)` \
		registry.heroku.com/releng-staging-$(subst deploy-staging-releng_,,$@)/web
	docker push \
		registry.heroku.com/releng-staging-$(subst deploy-staging-releng_,,$@)/web

deploy-staging-releng_frontend: require-AWS build-app-releng_frontend build-tool-awscli
	./result-tool-awscli/bin/aws s3 sync \
		--delete \
		--acl public-read  \
		result-$(subst deploy-staging-,,$@)/ \
		s3://$(subst deploy-,releng-,$(subst releng_,,$@))

deploy-staging-docs: require-AWS build-docs build-tool-awscli
	./result-tool-awscli/bin/aws s3 sync \
		--delete \
		--acl public-read  \
		result-docs \
		s3://releng-staging-docs






deploy-production-all: $(foreach app, $(APPS), deploy-production-$(app)) deploy-production-docs

deploy-production: require-APP deploy-production-$(APP)

deploy-production-releng_clobberer: docker-releng_clobberer
	if [[ -n "`docker images -q $(subst deploy-production-,,$@)`" ]]; then \
		docker rmi -f `docker images -q $(subst deploy-production-,,$@)`; \
	fi
	cat result-$(subst deploy-production-,docker-,$@) | docker load
	docker tag `docker images -q \
		$(subst deploy-production-,,$@)` \
		registry.heroku.com/releng-production-$(subst deploy-production-,,$@)/web
	docker push \
		registry.heroku.com/releng-production-$(subst deploy-production-,,$@)/web

deploy-production-releng_frontend: require-AWS build-app-releng_frontend build-tool-awscli
	./result-tool-awscli/bin/aws s3 sync \
		--delete \
		--acl public-read \
		result-$(subst deploy-production-,,$@)/ \
		s3://$(subst deploy-,releng-,$(subst releng_,,$@))

deploy-production-docs: require-AWS build-docs build-tool-awscli
	./result-tool-awscli/bin/aws s3 sync \
		--delete \
		--acl public-read  \
		result-docs \
		s3://releng-production-docs



update-all: \
	$(foreach tool, $(TOOLS), update-tools.$(tool)) \
	$(foreach app, $(APPS), update-$(app))

update: require-APP update-$(APP)

update-%: nix
	nix-shell nix/update.nix --argstr pkg $(subst update-,,$@)





build-tools: $(foreach tool, $(TOOLS), build-tool-$(tool))

build-tool: require-TOOL build-tool-$(TOOL)

build-tool-%: nix
	nix-build nix/default.nix -A tools.$(subst build-tool-,,$@) -o result-tool-$(subst build-tool-,,$@)





build-docs: nix
	nix-build nix/default.nix -A releng_docs -o result-docs


# --- helpers


require-TOOL:
	@if [[ -z "$(TOOL)" ]]; then \
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
	@if [[ -z "$(APP)" ]]; then \
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
	@if [[ -z "$$AWS_ACCESS_KEY_ID" ]] || \
		[[ -z "$$AWS_SECRET_ACCESS_KEY" ]]; then \
		echo ""; \
		echo "You need to specify AWS credentials, eg:"; \
		echo "  make deploy-production-releng_clobberer \\"; \
	    echo "       AWS_ACCESS_KEY_ID=\"...\" \\"; \
		echo "       AWS_SECRET_ACCESS_KEY=\"...\""; \
		echo ""; \
		echo ""; \
		exit 1; \
	fi

all: build-apps build-tools
