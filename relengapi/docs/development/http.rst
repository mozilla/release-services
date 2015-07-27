HTTP Helpers
============

Response Headers
----------------

.. py:function:: relengapi.lib.http.response_headers(*headers, [status_codes=..])

    :param headers: sequence of (header, value) tuples
    :param status_codes: apply only to these response status codes

    Returns a decorator for view functions which will add the given headers to non-error responses.
    Insert this decorator just after the ``route`` decorators and before ``apimethod`` or any permission-checking decorators.

    The matching status codes can be specified in a variety of ways:

        * as a function: ``status_codes=lambda c: 200 <= c < 300 or c == 302``
        * as a single code: ``status_codes=404``
        * as a class: ``status_codes=3xx``
        * as an iterable: ``status_codes=[200, 204, 302]``

Use this function as follows::

    @bp.route('/some/path')
    @http.response_headers(('cache-control', 'no-cache'), status_codes='2xx')
    @p.foo.bar.require()
    def my_view():
        ..
