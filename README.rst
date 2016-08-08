Welcome to relengapi
====================

Purspose of relengapi ... TODO

- Documentation: https://docs.relengapi.mozilla.org
- Issues: https://gitub.com/mozilla/build-relengapi/issues
- Code: https://gitub.com/mozilla/build-relengapi

Repository structure
====================

- ``app.json``

  Heroku file, needed to deploy Pull Requests.

- ``contribute.json``

  A JSON schema for open-source project contribution data.
  https://www.contributejson.org/

- ``CONTRIBUTING.rst``

  A short contribution instructions.

- ``flatten_requirements.py``

  Python script used by ``make install`` command to flatten all of the
  duplicated dependencies that are required by by all of the requirements.txt
  files.

- ``LICENSE.txt``

  Full text of Mozilla Public License Version 2.0 that all this code is
  licensed under.

- ``Makefile``

  Helper commands that can help you setup development environment
  (``install``), build docs (``docs``), run tests (``check``) and check for
  code style (``lint``).

  Run ``make help`` to see all of the possible commands.::

    % make help
	Please use \`make <target>\` where <target> is one of
	  install  install development environment for all subprojects
	  check    run tests for all the subprojects
	  docs     build documentation to docs/build
	  lint     check coding style for all the code
	  clean    remove all installed environments

- ``Procfile``

  A Procfile is a mechanism for declaring what commands are run by
  application’s dynos on the Heroku platform.

  More about Procile you can find at `Heroku documentation
  site<https://devcenter.heroku.com/articles/procfile>`.

- ``README.rst``

  This file.

- ``docs/``

  Sphinx documentation for whole project.

- ``requirements-dev.txt``

    TODO: need to refractor it to be used

- ``requirements.txt``

    A pip_'s requirements file that points to all runtime dependencies.

- ``run.py``

  Python script used by Heroku (via Procfile) to run correct application(s)
  based on ``APP`` variable.

- ``settings.py``

  Production relengapi settings file for Heroku.

- ``src/``

  Directory where we keep all our source code

  - ``relengapi_frontend/``

    Read its `README<src/relengapi_frontend/README.md` for more info.

  - ``relengapi_clobberer/``

    Read its `README<src/relengapi_clobberer/README.md` for more info.

.. _pip: https://pip.pypa.io
