Taskcluster integration
=======================


1. Running tests
----------------

First we check that all projects build successfully. This includes linting,
tests, etc...::

    % make build-all

This actually runs ``nix-build`` for all the projects in ``mozilla-releng``
repository.

.. todo:: what happens when this fails?

.. todo:: how to we prevent rebuilding projects if there is no changes


2. Deploying
------------

.. todo:: what happens if there are no changes to application. will it get
          redeployed?

If we are on ``staging`` or ``production`` branch we trigger deploy.::

    % make deploy-staging-all

or::

    % make deploy-production-all
