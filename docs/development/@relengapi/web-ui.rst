Web User Interface
==================

Releng API is, primarily, a REST API.
Big cool webapps based on the API should run on a different origin and use oAuth or some similar technology to talk to the Releng API.

However, the service has a web user interface for some limited purposes:

 * documentation
 * API management (including issuing tokens, managing permissions, and so forth)
 * small administrative UIs for blueprints
 * simple reports and statistics displays

Administrative UIs and reports should be the smaller portion of the blueprints they represent, and should be limited to a simple user interface for the underlying API.
If the UI will be widely used by more than a small group of administrators, or contains complex logic, then it should run on a different origin and access the Releng API remotely.

Template Engines
----------------

Flask uses a server-side template engine, Jinja2.
However, you should not expect to use that engine in designing a UI for a blueprint.
The relengapi base module uses it to construct the layout for pages, but the actual content is implemented using Angular templates.
The rationales for this decision are:

 * It's simpler -- one (very powerful!) templating engine to learn
 * It emphasizes the need for the UI to be based on the API, and not on server-side fanciness
 * It avoids conflicts -- Jinja2 and Angular both use the same delimiters, ``{{`` and ``}}``

Jinja2 Templates
----------------

As detailed above, Jinja2 templates are used only within the relengapi base, to control the overall layout of pages.
They should not be uesd in blueprints.

Layout
......

Templates should extend ``layout.html`` and add content to the appropriate blocks:

 * ``head`` - the HTML head; extend (with ``super()``), rather than overriding, this block
 * ``title`` - the page title
 * ``header`` - the in-page header
 * ``content`` - the content of the page, empty by default
 * ``footer`` - the in-page footer

A complete template might look like this:

.. code-block:: none

    {% entends "layout.html" %}
    {% block head %}
        {{ super() }}
        {{ head.stylesheet(url_for('static', filename='blink.css')) }}
    {% endblock %}
    {% block content %}
        <blink>We're bringing the blink element back!</blink>
    {% endblock %}

Rendering Templates
...................

Render templates using the normal Flask approach::

    from flask import render_template
    @route('/blink-is-back')
    def blink_is_back():
        return render_template('blink_is_back.html')

If you find yourself passing a great deal of data as template context, consider using an Angular template instead.

Header Link Macros
..................

To add a script to a single page, use the ``head.script`` Jinja2 macro:

.. code-block:: none

    {% extends "layout.html" %}
    {% block head %}
        {{ super() }}
        {{ head.script(url_for('myblueprint.static', filename='somescript.js')) }}
    {% endblock %}

Similarly, the ``head.stylesheet`` macro works for stylesheets:

.. code-block:: none

    {% extends "layout.html" %}
    {% block head %}
        {{ super() }}
        {{ head.stylesheet(url_for('myblueprint.static', filename='blueprint.css')) }}
    {% endblock %}

Adding Header Links to All Pages
................................

Extensions which wish to add content to the layout can use functionality defined in :class:`relengapi.lib.layout.Layout`, accessible at ``app.layout``.
In particular, :meth:`~relengapi.lib.layout.Layout.add_head_content` will add the given content to the ``head`` block of every page.
For the more common case of adding a script tag linking to an external file, :meth:`~relengapi.lib.layout.Layout.add_script` will create the necessary tag, given the URL.

These methods would typically be called in a blueprint's initialization code (via ``@bp.record``).

.. _angular-templates:

Angular Templates
-----------------

RelengAPI embeds Angular templates into the ``content`` block of an HTML page, so they do not include an HTML ``<head>`` or ``<body>`` element.
Instead, most begin with a ``<div>`` element.
RelengAPI handles loading any necessary Javascript and CSS files in the ``<head>`` element, but does not add an ``ng-app`` attribute -- that's up to the tmplate.

A simple template might look like this:

.. code-block:: html

    <div ng-app="widgets" ng-controller="WidgetController">
        <h1>Widgets</h2>
        <ul>
            <li ng-repeat="widget in widgets">
                {{widget.name}}: {{widget.description}}
            </li>
        </ul>
    </div>

Place this file in the blueprint's ``static`` folder, along with ``widgets.js``:

.. code-block:: javascript

    module('widgets', ['initial_data']).controller('WidgetController',
                                    function($scope, initial_data) {
        $scope.widgets = initial_data.widgets;
    });

The Flask view function to render this template (at the root of the blueprint) is

.. code-block:: python

    @bp.route('/')
    def ui():
        widgets = [w.to_jsonwidget() for w in Widget.query.all()]
        return angular.template('widgets.html',
                                url_for('.static', filename='widgets.js'),
                                widgets=widgets)

The next few sections will break down what all of that means!

Javascript Support
..................

RelengAPI includes the following Javascript libraries.
You may assume these are present in an Angular template.

 * `jQuery 1.11.1 <http://jquery.com/>`_
 * `Angular-1.2.9 <https://angularjs.org/>`_
 * `Alertify <http://fabien-d.github.io/alertify.js/>`_
 * `Bootstrap 3.3.1 <http://getbootstrap.com/getting-started/#download>`_
 * `Moment.js 2.8.4 <http://momentjs.com/>`_ and `Angular-Moment <https://github.com/urish/angular-moment>`_ (note that your module must depend on `'angularMoment'` to get this functionality)

Rendering an Angular Template
.............................

The Python code to render an Angular template faintly resembles normal Flask code to render a Jinja2 template, but uses :func:`angular.template <relengapi.lib.angular.template>` instead.

.. py:module:: relengapi.lib.angular

.. py:function:: template(template_name, *dependency_urls, **initial_data)

    :param template_name: name of the template file, relative to the app or blueprint's ``static_folder``
    :param dependency_urls: URLs (generated with ``url_for`` for any CSS or JS dependencies)
    :param initial_data: JSON-able data to be provided to the template as the ``initial_data`` constant in the ``initial_data`` module.

    Render an HTML page containing the named template in its ``content`` block.
    All of the dependency URLs are loaded in the ``<head>`` element.
    Any keyword arguments are JSONified and passed to the Angular app in the ``initial_data`` module.
    To use this data, depend on the module, and then inject ``initial_data``; see the example below.

The named template must contain an element with an ``ng-app`` attribute specifying a module of your devising, or Angular will do nothing.
Inside of that element, the Angular documentation applies as usual.
The module should be defined in a ``.js`` file specified as one of the dependency URLs.

Javascript best practices suggest supplying initial data for a page along with the page content, instead of making a separate AJAX request.
The ``initial_data`` arguments, Angular module, and Angular constant make this easy.
However, it's important that this data also be available via an API call.
The most common way to accomplish this is to invoke the actual API call using :py:func:`~relengapi.lib.api.get_data`.

The ``initial_data`` constant contains the following data in every template:

    * ``initial_data.user`` -- the current user
    * ``initial_data.perms`` -- all defined permissions, in the form of a map from permission name to permission documentation.

Putting all of this together::

    @bp.route('/')
    def root():
        return angular.template('widgets.html',
                                url_for('.static', filename='widgets.js'),
                                widgets=api.get_data(list_widgets))

    @bp.route('/widgets')
    @p.base.widgets.view.require()
    @apimethod([JsonWidget])
    def list_widgets():
        return [JsonWidget(w.id, w.name) for w in Widgets.query.all()]

Here, the blueprint's ``/`` path is the Angular UI, based on ``widgets.html`` and ``widgets.js``, both in the blueprint's ``static`` directory.
The ``initial_data`` includes a full list of widgets, from ``list_widgets``.
If the user doesn't have the ``base.widgets.view`` permission, the ``get_data`` call will raise an exception and the view will not be rendered.

Alertify
........

Note that ``alertify`` is a global variable, not an Angular module.
To alert the user, use something as simple as

.. code-block:: javascript

    alertify.success("token issued");

Angular Directives
..................

The following directives are available in any Angular template that requires the ``relengapi`` module:

 * ``<perm name="foo.bar" />`` -- renders a permission name

Angular Services
................

The ``relengapi`` module provides a number of useful services, and is loaded automatically.
Include it as a dependency of your angular module, then use dependency injection to access the services.

restapi
:::::::

The ``restapi`` service is a wrapper around the standard ``$http`` service, specifically designed to make calls to the RelengAPI REST API.
It automatically catches and invokes Alertify for any errors from the API before passing the failure along unchanged.
Thus most API calls can omit any failure handling.

To make the message a bit more clear to the user, include a value for ``while`` in the ``config`` parameter, giving a clause describing the action.
For example:

.. code-block:: javascript

    restapi.get('/some/interesting/details', {while: 'getting interesting details'}).then(..);

If some response statuses are expected and should not trigger an error, list them with ``expectedStatus`` or ``expectedStatuses``:

.. code-block:: javascript

    restapi.get('/some/interesting/details', {expectedStatus: 404}).then(..);
    restapi.get('/some/interesting/details', {expectedStatuses: [404, 409]}).then(..);

Root Widgets
------------

TODO: refactor to use Angular with ngInclude

The root page of the RelengAPI contains "widgets" that can be provided by installed blueprints.
To add such a widget, define a template for the widget and add it to the blueprint with ``bp.root_widget_template``::

    bp.root_widget_template('myproject_root_widget.html', priority=10)

The priority defines the order of the widgets on the page, with smaller numbers appearing earlier.

The function also accepts a ``condition`` argument, which is a callable that will determine whether the widget should be displayed.
This condition might, for example, look at whether the user has permission to use the blueprint.

Shipping Templates and Static Files
-----------------------------------

To use static files (including Angular templates) in your blueprint, include ``static_folder='static'`` in the constructor arguments, and add a ``static`` directory

.. code-block:: none

    relengapi/blueprints/mypackage/__init__.py
    relengapi/blueprints/mypackage/static

Use ``url_for('.static', filename='somefile.js')`` to generate static URLs (noting the leading dot).
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

To use Jinja2 templates in your blueprint, well, you shouldn't.
But if you insist, include ``template_folder='templates'`` in the constructor arguments, and add a ``templates`` directory

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
