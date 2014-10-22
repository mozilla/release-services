RelengAPI-Clobberer
===================

Keeping intermediate files around after a build helps make subsequent runs faster since it acts as form of local caching.
Unfortunately this can lead to corruption in some circumstances. If a developer notices that their CI/try jobs are failing due 
to corrupted build directories they should have the option to reset the build directory to a clean state - i.e. clobber it.

This is the API for clobbering build directories on buildbot slaves in Mozilla's CI infrastructure.

Documentation
-------------

For documentation about clobberer and its various endpoints see https://api.pub.build.mozilla.org/docs/usage/clobberer

Development
-----------

Layout
~~~~~~

Clobberer is a `Flask Blueprint`_ which plugs into RelengAPI.

.. _Flask Blueprint:  http://flask.pocoo.org/docs/blueprints/

Running Clobberer
~~~~~~~~~~~~~~~~~

To run the tool for development, pip install the requirements into your virtualenv:

    pip install -e .[test]

The `[test]` installs the requirements for testing as well.
Omit this if you won't be running tests.

[optional] Build the docs:

    relengapi build-docs --development

Create the databases for the installed blueprints:

    relengapi createdb

And finally run the server:

    relengapi serve -p 8010

The `relengapi` tool has many useful subcommands.
See its help for more information.

Deployment
----------
See: https://wiki.mozilla.org/ReleaseEngineering/How_To/Update_RelengAPI
