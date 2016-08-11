.PHONY: help develop build-all build docker \
	deploy-staging-all deploy-staging \
	deploy-production-all deploy-production \
	update-all

APP=
APPS=relengapi_clobberer relengapi_frontend


help:
	@echo "TODO: need to write help for commands"


develop: require-APP
	nix-shell nix/default.nix -A $(APP) --run $$SHELL



build-all: build-$(APPS)

build: require-APP build-$(APP)

build-%:
	nix-build nix/default.nix -A $(subst build-,,$@) -o result-$(subst build-,,$@)



docker: require-APP docker-$(APP)

docker-%:
	rm -f result-$@
	nix-build nix/docker.nix -A $(subst docker-,,$@) -o result-$@



deploy-staging-all: deploy-staging-$(APPS)

deploy-staging: require-APP deploy-staging-$(APP)

deploy-staging-relengapi_clobberer: docker-relengapi_clobberer
	if [[ -n "`docker images -q $(subst deploy-staging-,,$@)`" ]]; then \
		docker rmi -f `docker images -q $(subst deploy-staging-,,$@)`; \
	fi
	cat result-$(subst deploy-staging-,docker-,$@) | docker load
	docker tag `docker images -q \
		$(subst deploy-staging-,,$@)` \
		registry.heroku.com/releng-staging-$(subst deploy-staging-,,$@)/web
	docker push \
		registry.heroku.com/releng-staging-$(subst deploy-staging-,,$@)/web

deploy-staging-relengapi_frontend: require-AWS build-relengapi_frontend tools-awscli
	./result/bin/aws s3 sync \
		--delete \
		--acl public-read  \
		result-$(subst deploy-staging-,,$@)/ \
		s3://$(subst deploy-,releng-,$(subst _,-,$@))





deploy-production-all: deploy-production-$(APPS)

deploy-production: $(APP) deploy-production-$(APP)

deploy-production-relengapi_clobberer: docker-relengapi_clobberer
	if [[ -n "`docker images -q $(subst deploy-production-,,$@)`" ]]; then \
		docker rmi -f `docker images -q $(subst deploy-production-,,$@)`; \
	fi
	cat result-$(subst deploy-production-,docker-,$@) | docker load
	docker tag `docker images -q \
		$(subst deploy-production-,,$@)` \
		registry.heroku.com/releng-production-$(subst deploy-production-,,$@)/web
	docker push \
		registry.heroku.com/releng-production-$(subst deploy-production-,,$@)/web

deploy-production-relengapi_frontend: require-AWS build-relengapi_frontend tools-awscli
	./result/bin/aws s3 sync \
		--delete \
		--acl public-read \
		result-$(subst deploy-production-,,$@)/ \
		s3://$(subst deploy-,releng-,$(subst _,-,$@))



update-all: \
	update-nixpkgs \
	update-tools \
	update-$(APPS)

update-%:
	echo $@
	nix-shell nix/update.nix --argstr pkg $(subst update-,,$@)



# --- helpers

tools-awscli:
	nix-build nix/default.nix -A tools.awscli -o result-awscli

require-APP:
	@if [[ -z "$(APP)" ]]; then \
		echo ""; \
		echo "You need to specify which APP, eg:"; \
		echo "  make develop APP=relengapi_clobberer"; \
		echo "  make build APP=relengapi_clobberer"; \
		echo "  ..."; \
		echo ""; \
		echo "Available APPS are: "; \
		for app in "$(APPS)"; do \
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
		echo "  make deploy-production-relengapi_clobberer \\"; \
	    echo "       AWS_ACCESS_KEY_ID=\"...\" \\"; \
		echo "       AWS_SECRET_ACCESS_KEY=\"...\""; \
		echo ""; \
		echo ""; \
		exit 1; \
	fi
