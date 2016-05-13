
NPM=npm
VIRTUALENV=virtualenv
PYTHON=./env/bin/python
PIP=./env/bin/pip
FLAKE8=./env/bin/flake8
PYTEST=./env/bin/py.test
ENV=./env

.PHONY: help
help:
	@echo "Commands:"
	@echo ""
	@echo "  install		TODO..."
	@echo "  check			TODO..."
	@echo "  docs			TODO..."
	@echo "  lint			TODO..."
	@echo "  clean			TODO..."


.PHONY: install
install: env
	rm -f requirements-flatten.txt
	$(PYTHON) flatten_requirements.py requirements-dev.txt requirements-flatten.txt
	$(PIP) install -r requirements-flatten.txt
	cd src/relengapi_tools && $(NPM) install

.PHONY: lint
lint:
	$(FLAKE8) \
			run.py \
			flatten_requirements.py \
			src/relengapi_clobberer/setup.py \
			src/relengapi_clobberer/relengapi_clobberer
	cd src/relengapi_tools && $(NPM) run build

.PHONY: docs 
docs:
	cd docs/ && $(MAKE) html

.PHONY: check
check:
	$(PYTEST) \
			src/relengapi_clobberer/tests/
	cd src/relengapi_tools && $(NPM) run test

.PHONY: env
env:
	$(VIRTUALENV) $(ENV)

.PHONY: clean
clean:
	rm -rf $(ENV)
	rm -rf src/relengapi_tools/node_modules/

.PHONY: clean
requirements-dev.txt: clean env
	rm -f requirements-dev.txt
	$(PIP) install Sphinx pytest flake8
	$(PIP) freeze | grep -v relengapi- > requirements-dev.txt
