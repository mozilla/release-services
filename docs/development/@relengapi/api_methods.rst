API Methods
===========

The Releng API is primarily a host for a REST API.
While it's generally easy to implement this with a plain Flask view function, Releng API has some additional support to help make the API behave consistently for consumers.

This support includes a fixed JSON format for API responses.
The response is always an object, and for a success (2xx) response, has a ``result`` key containing the result.
For error responses, an ``error`` key contains information about the error.

Types
-----

A REST API implements *Representative State Transfer*, meaning that it involves transferring representations of entities back and forth.
Those entities have a type which describes their contents.

Releng API makes use of WSME_'s type model.
Simple, atomic types like ``unicode`` and ``int`` are described with their Python types.
Compound types are defined by subclassing ``wsme.types.Base``::

    class Widget(wsme.types.Base):
        """A model of widget available from our Widget supplier."""

        #: unique ID
        id = integer

        #: latest unit price, in USD
        price = integer

        #: supplier's stock code
        stock_code = unicode

See the WSME_ documentation for more detail.

As a utility, an arbitrary JSON Object can be described with this class:

.. attribute:: relengapi.lib.api.jsonObject

    A WSME custom type describing an arbitrary JSON object.
    This validates that the value is an object (equivalent to a ``dict`` in Python) and that it can be JSON-encoded.

Decorator
---------

All API view methods should be wrapped with :py:func:`~relengapi.lib.api.apimethod`, which is available in the ``relengapi`` namespace::

    from relengapi import apimethod
    ...
    @bp.route('/widget/<int:widget_id>')
    @apimethod(Widget, int)
    def get_widget(widget_id):
        "Get a widget, identified by id"
        widget = ...
        return widget

The ``@apimethod`` decorator takes the same arguments as WSME's @\ signature_ decorator.
In short, this means the return type of the method followed by the argument types.
Arguments may be included in the URL, if specified in the route.
Otherwise, they are assumed to be query arguments (after ``?`` in the URL).

The view function docstring is copied into the generated endpoint documentation.
Any paragraph-level reStructured Text is valid.

The view function should return its results (or None, if there are no interesting results) as a Python object of the appropriate type.
In the example above, ``widget`` should be an instance of the ``Widget`` class defined above.
The decorator will take care of converting this to JSON, including HTML framing for display in a browser.

To return a success code other than 200 or include headers, simply return a tuple like from a regular View Function. ::

    return new_widget, 201
    # or
    return new_widget, 201, {'X-Widget-Id': new_widget.id}

.. py:function:: relengapi.lib.api.apimethod(*args, **kwargs)

    Returns a decorator for API methods as described above.
    The arguments are those for WSME's @\ signature_ decorator.


Non-REST Endpoints
..................

Sometimes endpoints don't take or return JSON documents.
For user convenience, this should be minimized.

In cases where this is necessary, the ``apimethod`` decorator can't be used.
Instead, your view function must do any encoding, decoding, and error handling itself.
See below for help documenting such endpoints.

Exceptions
----------

Within a browser, exceptions are handled as they would be for any Flask application.
HTTP Exceptions are rendered with the proper status code, while others result in a simple 500 ISE.
When debugging is enabled, non-HTTP exceptions render a traceback.

However, when the request does not specify ``text/html``, the exception is encoded as JSON.
HTTP Errors again have the appropriate status code, while other exceptions are treated as 500 ISE's.
The ``error`` key of the returned JSON contains keys ``code``, ``name``, and ``description``.
When debugging is enabled, the exception information also contains a ``traceback`` key.

.. _api-documentation:

Documentation
-------------

Endpoints
.........

Documentation for API endpoints is generated based on the information in the source code.
Insert the generated documentation at the appropriate place using the ``api:autoendpoint`` directive, which takes a list of patterns matching Flask enpoint names.

The generated documentation is based on the docstring for the view function, along with the types specified with the ``apimethod`` decorator and the routes specified with the ``route`` decorator.

For example, if the ``get_widget`` view function, above, is part of the ``widgets`` blueprint, then its documentation file would reference it as

.. code-block:: none

    .. api:autoendpoint:: widgets.get_widget

The directive takes a list of glob patterns, so documenting all endpoints in a blueprint is as easy as

.. code-block:: none

    .. api:autoendpoint:: widgets.*

Or, if you prefer to control the order:

.. code-block:: none

    .. api:autoendpoint::
        widgets.list_widgets
        widgets.new_widget
        widgets.update_widget
        widgets.delete_widget

Types
.....

REST API Types are similar: the content of the documentation comes from the source code, but the positioning is controlled by the ``.rst`` file.

Type information is drawn from the docstring for the type class as well as the Sphinx-style comments for each attribute.
These comments have the special prefix ``#:``.
See the ``Widget`` class above for an example.

To document a type or types, use ``api:autotype::``, like this:

.. code-block:: none

    .. api:autotype:: VersionInfo BlueprintInfo

This will document the types in the order they are given.

References
..........

Types can be referenced using the prefix ``:api:type``, e.g.,

.. code-block:: none

    Each :api:type:`Mapping` will be processed in order.

Similarly, endpoints are referenced using their Flask endpoint name, e.g.,

.. code-block:: none

    Use :api:endpoint:`tokenauth.issue_token` to issue tokens.

Non-REST Endpoints
..................

Endpoints which aren't sufficiently RESTful to be automatically documented can be described with the ``endpoint`` directive:

.. code-block:: none

    .. endpoint:: endpoint.name
        POST /foo/<name>
        PATCH /foo/<name>

        :param name: name of the foo
        :body: foo document
        :response: updated foo document

        Update or set the contents of a Foo.
        With PATCH, the new and existing foo documents will be merged.

The first argument is the name of the endpoint (usually the dotted combination of the blueprint and function name).
The remaining arguments alternate between method names and paths.

The docfields are ``param`` for request parameters, ``body`` for the request body, and ``response`` for the response body.

Getting Data
------------

If you need the data from an API method (e.g., to pass it to an :ref:`Angular template <angular-templates>`), pass the view function to :py:func:`relengapi.lib.api.get_data`, passing additional arguments as necessary. ::

    widget_info = api.get_data(get_widgets, widget_id)

This function will raise an exception if the current request does not have proper permission.

.. _WSME: http://wsme.readthedocs.org/
.. _signature: http://wsme.readthedocs.org/en/latest/api.html#wsme.signature
