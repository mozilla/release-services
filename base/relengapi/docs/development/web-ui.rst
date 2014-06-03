Web User Interface
==================

Releng API is, primarily, a REST API.
Big cool webapps based on the API should run on a different origin and use oAuth or some similar technology to talk to the Releng API.

However, the service has a web user interface for some limited purposes:

 * documentation
 * API management
 * small administrative UIs for blueprints

Management of the API includes issuing tokens, managing permissions, and so forth.

Administrative UIs should be the smaller portion of the blueprints they represent.
If the UI will be widely used by more than a small group of administrators, then it should run on a different origin and access the Releng API remotely.

Implementing UIs
----------------

A UI can use Flask templates to render HTML pages for the UI at certain URLs, intermingled freely with API URLs.
Often this begins at the root of the blueprint.

Forms and interactive elements on these pages should make ordinary API calls, rather than submitting forms via the browser's support.
In other words, the UI should provide a human interface to the API, but must not allow any behavior that could not be implemented directly with the API.

A good rule of thumb is to treat the administrative UI as a "rough draft".
If issues with the UI bother users enough, they can implement their own, better UI on another origin with no loss in functionality.

Layout
------

Templates should extend ``layout.html`` and add content to the appropriate blocks:

 * ``head`` - the HTML head; extend, rather than overriding, this block
 * ``title`` - the page title
 * ``header`` - the in-page header
 * ``content`` - the content of the page, empty by default
 * ``footer`` - the in-page footer

Extensions or blueprints which wish to add content to the layout can use functionality defined in :class:`relengapi.lib.layout.Layout`, accessible at ``app.layout``.
In particular, :meth:`~relengapi.lib.layout.Layout.add_head_content`` will add the given content to the ``head`` block of every page.

For the more common case of adding a script tag linking to an external file, :meth:`~relengapi.lib.layout.Layout.add_script`` will create the necessary tag, given the URL.

Javascript Support
------------------

The layout templates include the following Javascript libraries.
UI code may assume these are present.

 * `jQuery 1.7.2 <http://jquery.com/>`_
 * `Alertify <http://fabien-d.github.io/alertify.js/>`_

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
    However, the ``validate.sh`` script will catch such issues.

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

The function also accepts a ``condition`` argument, which is a callable that will determine whether the widget should be displayed.
This condition might, for example, look at whether the user has permission to use the blueprint.
