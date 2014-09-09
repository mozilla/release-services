Writing a Blueprint
===================

If your blueprint will be meaty enough to deserve its own project, repo, and so forth, then start that now.
Otherwise, if it's just a small thing, add it to the relengapi project in a top-level directory.
Note that Releng Best Practices call for many well-delineated projects, so err on the former side.

Add a ``setup.py`` similar to that in ``docs/``.
Name the package with a ``relengapi-`` prefix, so it's easy to find.
The ``install_requires`` parameter should name both ``Flask`` and ``relengapi``, as well as any other dependencies.
The ``namespace_packages`` line allows multiple packages to share the same Python path::

    namespace_packages=['relengapi', 'relengapi.blueprints'],

Include a ``package_data`` section to capture any templates, static files, or documentation::

    package_data={  # NOTE: these files must *also* be specified in MANIFEST.in
        'relengapi': ['docs/**.rst'],
        'relengapi.blueprints.base': [
                'templates/**.html',
                'static/**.jpg',
                'static/**.css',
                'static/**.js',
                'static/**.txt',
            ],
    },

Finally, include an entry point so that the base can find the blueprint::

    entry_points={
        "relengapi.blueprints": [
            'mypackage = relengapi.blueprints.mypackage:bp',
        ],
    },

The ``relengapi.blueprints.mypackage:bp`` in the above is an import path leading to the Blueprint object.

Now, create the directory structure

.. code-block:: none

    relengapi/__init__.py
    relengapi/blueprints/__init__.py
    relengapi/blueprints/mypackage/__init__.py

The first two of the ``__init__.py`` files must have *only* the following contents::

    __import__('pkg_resources').declare_namespace(__name__)

In the third, create your Blueprint::

    from flask import Blueprint, jsonify
    bp = Blueprint('mypackage', __name__)
    @bp.route('/some/path')
    def root():
        return jsonify("HELLO")

The ``root`` function in this example would be available at ``/mypackage/some/path``.

Note that all RelengAPI blueprints are available in dictionary ``current_app.relengapi_blueprints``.
Each has a ``dist`` attribute giving the SetupTools distribution from which the blueprint came.

The remaining sections in this chapter describe what you can do with your new blueprint.
