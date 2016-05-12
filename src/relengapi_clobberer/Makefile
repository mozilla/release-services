
PYPI2NIX=pypi2nix
VIRTUALENV=virtualenv
ENV=./env

help:

env: clean-env
	$(VIRTUALENV) $(ENV)
	$(ENV)/bin/pip install -e ../relengapi_common -e ../relengapi_clobberer gunicorn psycopg2

develop:
	RELENGAPI_SETTINGS=$(PWD)/settings.py $(ENV)/bin/python relengapi_clobberer/__init__.py

requirements.txt: clean-requirements
	$(ENV)/bin/pip freeze | grep -v relengapi- > requirements.txt

nix: clean-nix
	cat requirements.txt | grep -v relengapi_ | grep -v wheel > python-packages.txt
	$(PYPI2NIX) -r python-packages.txt


clean-env:
	rm -rf $(ENV) 

clean-requirements:
	rm -f requirements.txt

clean-nix:
	rm -f python-packages.txt \
		  python-packages.nix \
		  python-packages_generated.nix

clean: clean-env clean-requirements clean-nix
