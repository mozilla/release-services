.. _develop-python-project:

Python project
==============

- Runtime dependencies (install_requires) are listed in
  ``src/<project>/requirements.txt``

- Buildtime dependencies (tests_require) are listed in 
  ``src/<project>/requirements-dev.txt``

- Like every python project also our project has a ``src/<project>/setup.py``

  Use ``requirements.txt`` and ``requirements-dev.txt`` to list dependencies.
  That way we only change

  Every time you add/remove/update dependencies rereun::

      % ./please tools update-dependencies <project>

  More information about updating dependencies you can find here (TODO: link)

- Your python module should be named the same as the project, that means that
  the code for your  python module will be located in
  ``src/<project>/<project>/``

- (TODO: needs to be implemented) to create an empty python project

- different helper modules in cli_common



