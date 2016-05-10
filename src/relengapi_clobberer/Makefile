
PYPI2NIX=pypi2nix
VIRTUALENV=virtualenv
ENV=./env

help:

env: clean-env
	$(VIRTUALENV) $(ENV)
	$(ENV)/bin/pip install -e ../relengapi_common -e ../relengapi_clobberer gunicorn

develop:
	RELENGAPI_SETTINGS=$(PWD)/settings.py $(ENV)/bin/python relengapi_clobberer/__init__.py

requirements.txt: env clean-requirements
	echo "-e ../relengapi_common" > requirements.txt
	echo "-e ../relengapi_clobberer" >> requirements.txt
	$(ENV)/bin/pip freeze | grep -v relengapi- >> requirements.txt

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
