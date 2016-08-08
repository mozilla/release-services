.PHONY: help develop build update

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  develop  install and enter development environment"
	@echo "  build    update nix expressions to latest"
	@echo "  update   run tests for all the subprojects"


develop:
	nix-shell

build:
	nix-build

update: update-requirements update-relengapi_frontend update-shipit_frontend

update-requirements:
	pypi2nix -v -V 3.5 -r requirements.txt -r requirements-prod.txt -r requirements-dev.txt -E "postgresql"

update-relengapi_frontend:
	cd src/relengapi_frontend && node2nix --flatten --pkg-name nodejs-6_x

update-shipit_frontend:
	cd src/shipit_frontend && node2nix --flatten --pkg-name nodejs-6_x
