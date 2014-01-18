RelengAPI
=========

Your Interface to Release Engineering Automation.

Users
-----

Haha, not yet.

Developers
----------

### Structure

RelengAPI is a Flask application.  It is composed of several Python packages.

The base is `relengapi`.
It implements the root app, and lots of other common features.
It also searches its python environment for other packages that can provide blueprints for the Releng API.
These act as plugins, adding extra endpoints and other functionality to the API.

The `relengapi-docs` package implements the documentation tree for the Releng API, and is a prototypical blueprint package.

### Running

To run the tool for development, pip install the base into your virtualenv:

    pip install -e base

and any blueprints you want:

    pip install -e docs

Set up your settings file:

    cp settings_example.py settings.py
    vim settings.py
    export RELENGAPI_SETTINGS=$PWD/settings.py

Create the databases for the installed blueprints:

    relengapi createdb

And finally run the server:

    relengapi serve -p 8010

The `relengapi` tool has many useful subcommands.
See its help for more information.
If you've installed the `docs` blueprint, then the API documents itself via HTTP -- just visit with a browser.
See the Releng API documentation for more information on development and deployment of the releng API.
