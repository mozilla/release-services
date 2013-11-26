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
These act as plugins, adding extra endpoints to the API.

The `relengapi-docs` package implements the documentation tree for the Releng API, and is a prototypical blueprint package.

### Running

To run the tool for development, pip install the base:

    pip install -e base

and any Blueprints you want:

    pip install -e docs

then run `relengapi` to run the server in the foreground.
This tool has some command-line options that may be useful; see its `--help`.

### Writing a Blueprint

If your blueprint will be meaty enough to deserve its own project, repo, and so forth, then start that now.
Otherwise, add it to the relengapi project in a top-level directory.

Add a `setup.py` similar to that in `docs/`.
Name the package with a `relengapi-` prefix, so it's easy to find.
The `install_requires` parameter should name both `Flask` and `relengapi`, as well as any other dependencies.
The `namespace_packages` line allows multiple packages to share the same Python path:

    namespace_packages=['relengapi.blueprints'],

Finally, include an entry point so that the base can find the blueprint:

    entry_points={
        "relengapi_blueprints": [
            'mypackage = relengapi.blueprints.mypackage:bp',
        ],
    },

The `relengapi.blueprints.mypackage:bp` in the above is an import path leading to the Blueprint object.

Finally, create the directory structure:

    relengapi/__init__.py
    relengapi/blueprints/__init__.py
    relengapi/blueprints/mypackage/__init__.py

The first two of the `__init__.py` files must have *only* the following contents:

    __import__('pkg_resources').declare_namespace(__name__)

In the third, create your Blueprint:

    from flask import Blueprint, jsonify
    bp = Blueprint('docs', __name__)
    @bp.route('/some/path')
    def root():
        return jsonify("HELLO")

This function would be available at `/mypackage/some/path`.
