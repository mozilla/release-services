.PHONY: help develop build update

help:
	@echo "Please use \`make <target>' where <target> is one of"


develop-clobberer:
	nix-shell -A relengapi_clobberer

check-clobberer:
	nix-build -A relengapi_clobberer

docker-clobberer:
	rm -f result-clobberer
	nix-build release.nix -A docker.relengapi_clobberer -o result- clobberer

deploy-clobberer-staging: docker-clobberer
	if [[ -n "`docker images -q registry.heroku.com/releng-clobberer-staging/web`" ]]; then \
			docker rmi -f registry.heroku.com/releng-clobberer-staging/web; \
		fi
	if [[ -n "`docker images -q relengapi_clobberer`" ]]; then \
			docker rmi -f `docker images -q relengapi_clobberer`; \
		fi
	cat result-clobberer | docker load
	docker tag `docker images -q relengapi_clobberer` registry.heroku.com/releng-clobberer-staging/web
	docker push registry.heroku.com/releng-clobberer-staging/web
