HTTP Helpers
============

Response Headers
----------------

.. py:function:: relengapi.lib.http.response_headers(*headers)

    :param headers: sequence of (header, value) tuples

    Returns a decorator for view functions which will add the given headers to non-error responses.
    Insert this decorator just after the ``route`` decorators and before ``apimethod`` or any permission-checking decorators.

Use this function as follows::

    @bp.route('/some/path')
    @http.response_headers(('cache-control', 'no-cache'))
    @p.foo.bar.require()
    def my_view():
        ..
