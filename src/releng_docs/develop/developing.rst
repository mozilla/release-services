================
Start Developing
================


.. todo::

    Describe how to use please command once implemented and the benefits of it.
    Write that Docker or Nix are required to use please command


Not using ``please`` command.
=============================

Any python project can easily be installed using a more familiar
**virtualenv+pip**. You will have to install system dependencies yourself (eg.
postgresql, libxml2, ...) and also provide needed configuration variables.

To install ``shipit_taskcluster`` using **virtualenv + pip** do:

.. code-block:: console

    $ git clone git@github.com:mozilla-releng/services.git
    $ cd services/src/shipit_taskcluster
    $ virtualenv env
    $ ./env/bin/pip install -r requirements.txt -r requirements-dev.txt
    $ ./env/bin/pip install -e .

For linting of our code we use **flake8** which gets installed via
``requirements-dev.txt`` and is configured in ``setup.cfg``:

.. code-block:: console

    $ ./env/bin/flake8

To run tests we us **pytest** test framework and you need to :

.. code-block:: console

    $ ./env/bin/pytest tests/

To start the application you are developing you can do:

.. code-block:: console

    $ export DATABASE_URL="postgresql://...."
    $ export FLASK_APP=shipit_taskcluster.flask:app
    $ flask run

Variables which are required are described in ``settings.py`` configuration
file. Most likely you will need to configure ``DATABASE_URL`` which will point
to you development instance of Postgresql.
