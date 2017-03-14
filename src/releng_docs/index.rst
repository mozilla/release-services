Mozilla Release Engineering Services
====================================

A goal of *Release Engineering Services* is to *converge efforts* to
**develop**, **test**, **deploy**, **maintain**, and most importantly
**document** all services that *Release Engineering Team* is providing or
supporting.

    Currently supported platform is **Linux**.

Useful links
------------

:Code: https://github.com/mozilla-releng/services
:Issues: https://github.com/mozilla-releng/services/issues
:Documentation: https://docs.mozilla-releng.net


Repository structure
--------------------

- **src/**: folder with all the services
- **src/<service>**: folder with a <service> sources
- **lib/**: sources of libraries to help build services in **src/**
- **nix/**: all nix related tools
- **Makefile**: helper utilities


Quickstart
----------

Read :ref:`prerequirements`

Get code:

.. code-block:: bash

    % git clone https://github.com/mozilla-releng/services
    % cd services/
    % make  # will display help

Start **developing** a service:

.. code-block:: bash

    % make develop APP=<service>

Running service in **develop** mode (eg. restarting when source files changes):

.. code-block:: bash

    % make develop-run APP=<service>

Run **tests**:

.. code-block:: bash

    % make build-app APP=<service>

Services get automatically **deployed** when code gets merged into ``staging``
or ``production``.


Contents
--------

.. toctree::
    :maxdepth: 2

    prerequirements
    developing
    continuous-integration
    deploying
    contributing
    authentication
    services_releng
    services_shipit
    defending
    database_migrations
