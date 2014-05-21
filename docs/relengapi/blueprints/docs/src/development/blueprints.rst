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

Finally, include an entry point so that the base can find the blueprint::

    entry_points={
        "relengapi_blueprints": [
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
    bp = Blueprint('docs', __name__)
    @bp.route('/some/path')
    def root():
        return jsonify("HELLO")

The ``root`` function in this example would be available at ``/mypackage/some/path``.  

Templates
---------

To use templates in your blueprint, include ``template_folder='templates'`` in the constructor arguments, and add a ``templates`` directory

.. code-block:: none

    relengapi/blueprints/mypackage/__init__.py
    relengapi/blueprints/mypackage/templates/

You must also add this to your ``setup.py``::

    package_data={  # NOTE: these files must *also* be specified in MANIFEST.in
        'relengapi.blueprints.mypackage': [
            'templates/*.html',
        ],
    },

and to your ``MANIFEST.in``:

.. code-block:: none

    recursive-include relengapi/blueprints/mypackage/templates *.html

.. warning::

    It's easy to add new files and forget to update one of ``setup.py`` or ``MANIFEST.in``.
    The Python packaging tools provide no warning about this error, either.

.. warning::

    Jinja2 treats template names as a flat namespace.
    If multiple blueprints define templates with the same name, the results are undefined.
    Name your templates uniquely -- prefixing with the blueprint name is an effective strategy.

Static
------

To use static files in your blueprint, include ``static_folder='static'`` in the constructor arguments, and add a ``static`` directory

.. code-block:: none

    relengapi/blueprints/mypackage/__init__.py
    relengapi/blueprints/mypackage/static

Use ``url_for('mypackage.static', filename='somefile.js')`` to generate static URLs.
Unlike templates, URLs are scoped to the blueprint, so there is no risk of filename collisions.

You must also add the static files to your ``setup.py``::

    package_data={  # NOTE: these files must *also* be specified in MANIFEST.in
        'relengapi.blueprints.mypackage': [
            'static/*.js',
            'static/*.css',
        ],
    },

and to your ``MANIFEST.in``:

.. code-block:: none

    recursive-include relengapi/blueprints/mypackage/static *.js
    recursive-include relengapi/blueprints/mypackage/static *.css


Root Widgets
------------

The root page of the RelengAPI contains "widgets" that can be provided by installed blueprints.
To add such a widget, define a template for the widget and add it to the blueprint with ``bp.root_widget_template``::

    bp.root_widget_template('myproject_root_widget.html', priority=10)

The priority defines the order of the widgets on the page, with smaller numbers appearing earlier.
