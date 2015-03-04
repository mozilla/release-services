RelengAPI
=========

Continuous Integration: https://travis-ci.org/mozilla/build-relengapi

Your Interface to Release Engineering Automation.

This is the framework behind https://api.pub.build.mozilla.org/.
It is a Flask-based framework for building and hosting releng-related APIs.

Goals
-----

 * Simple self-service usage for consumers
   * Industry-standard access mechanisms (REST, oAuth2, etc.) that require no client-side custom libraries
   * One or very few endpoints (e.g., https://api.pub.build.mozilla.org)
   * Self-documenting tools
   * Semantic versioning 

 * Simple, rapid implementation of new apps
   * Common requirements such as authentication, database access, scheduled tasks, configuration handling are already satisfied
   * All apps use the same technologies (language, web framework, DB framework, etc.), so the learning curve from one app to the next is small
   * Tailored for easy local development - minimal requirements, minimal installed components, etc. 

 * Operations-friendly
   * Horizontally scalable using normal webops techniques
   * Easily deployed in multiple environments with normal devops processes
   * Resilient to failure: no in-memory state 

Documentation
-------------

RelengAPI documents itself.  
See https://api.pub.build.mozilla.org/docs for the documentation of the currently-deployed version.

Info for Developers
-------------------

See the "Installation" page of the deployment documentation for information on required operating system packages.

### Structure

RelengAPI is a [Flask](http://flask.pocoo.org/) application.  It is composed of several Python distributions (packages).
Each distribution can contain several [Flask Blueprints](http://flask.pocoo.org/docs/blueprints/) -- web application components.
Each Git repository can contain multiple distributions.

The base is in the `relengapi` distribution, implemented in this package.
It implements the root app, with lots of common support functionality, and a number of blueprints.
It also searches its python environment for other distributions that can provide blueprints for the Releng API.
These act as plugins, adding extra endpoints and other functionality to the API.

Other top-level directories of this repository contain other related distributions with more blueprints.
Other repositories contain even more distributions, with even more blueprints.

All of this is drawn together in production by installing the appropriate distributions on the releng web cluster.
When developing, though, only the `relengapi` distribution and the distribution you're hacking on are required.

### Running RelengAPI

To run the tool for development, pip install the requirements into your virtualenv:

    pip install -e .[test]

The `[test]` installs the requirements for testing as well.
Omit this if you won't be running tests.

[optional] Build the docs:

    relengapi build-docs --development

[optional] Set up your settings file:

    cp settings_example.py settings.py
    vim settings.py
    export RELENGAPI_SETTINGS=$PWD/settings.py

Create the databases for the installed blueprints:

    relengapi createdb

And finally run the server:

    relengapi serve -p 8010

The `relengapi` tool has many useful subcommands.
See its help for more information.

### More

See the Releng API documentation for more information on development and deployment of the releng API.
This is available at https://api.pub.build.mozilla.org/docs or, If you've installed the `docs` blueprint, at the same path on your own instance.
