Quickstart guide
================

This guide should provide you a quick way to navigate through *Release
Engineering Services* and point you to instructions

Two tools are needed in your home environment ``git`` and ``gnumake``. Use your
system package manager to install them. Everything else will be provided by
build tools


Sources / Branches
------------------

To get code you need to clone `services`_ repository.

.. code-block:: bash

    % git clone https://github.com/mozilla-releng/services/
    % cd services/
    % git branch --list -r
    origin/master
    origin/production
    origin/staging
    
In above command we also listed all remote branches. To describe what each
branch is for:

- ``master``: The main development branch.
- ``staging``: The staging (eg. before production) branch, where all services are
  automatically deployed and are accessible under
  <service>.staging.mozilla-releng.net
- ``production``: The production branch, where all services are also
  automatically deployed and are accessible under <service>.mozilla-releng.net.

For more details of deployments, please look at specific service documentation
(eg: documentation for :ref:`Clobberer service <service-clobberer>`).

When submitting a **pull request** a build job for each service is being ran to
ensure that all tests across services are passing before you consider merging
it.


Development
-----------

To enter a shell and start developing an application do:

.. code-block:: bash

    % make develop APP=releng_clobberer


To run a application in development mode do:

.. code-block:: bash

    % make develop-run APP=releng_frontend

Application will get restarted on every save you do in the source code.

A list of available applications you can find by running:

.. code-block:: bash

    % make
    ...
    Available APPs are: 
     - releng_docs
     - releng_clobberer
     - releng_frontend
     - shipit_dashboard
     - shipit_frontend
     ...


Testing
-------





.. _`services`: https://github.com/mozilla-releng/services
