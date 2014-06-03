API Methods
===========

The Releng API is primarily a host for a REST API.
While it's generally easy to implement this with a plain Flask view function, Releng API has some additional support to help make the API behave consistently for consumers.

This support includes a fixed JSON format for API responses.
The response is always an object, and for a success (2xx) response, has a ``result`` key containing the result.
For error responses, an ``error`` key contains information about the error.

Decorator
---------

First, all API view methods should be wrapped with :py:func:`~relengapi.lib.api.apimethod`, which is available in the ``relengapi`` namespace::

    from relengapi import apimethod
    ...
    @bp.route('/widgets')
    @apimethod()
    def get_widgets():
        widgets = ...
        return widgets

The view function simply returns its results (or None, if there are no interesting results).
The decorator will take care of converting this to JSON, including HTML framing for display in a browser.

To return a success code other than 200 or include headers, simply return a tuple like from a regular View Function. ::

    return new_widget, 201
    # or
    return new_widget, 201, {'X-Widget-Id': new_widget.id}

..py:function:: relengapi.lib.api.apimethod()

    Returns a decorator for API methods as described above.

Exceptions
----------

Within a browser, exceptions are handled as they would be for any Flask application.
HTTP Exceptions are rendered with the proper status code, while others result in a simple 500 ISE.
When debugging is enabled, non-HTTP exceptions render a traceback.

However, when the request does not specify ``text/html``, the exception is encoded as JSON.
HTTP Errors again have the appropriate status code, while other exceptions are treated as 500 ISE's.
The ``error`` key of the returned JSON contains keys ``code``, ``name``, and ``description``.
When debugging is enabled, the exception information also contains a ``traceback`` key.
