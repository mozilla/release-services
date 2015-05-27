HTTP Requests
=============

The simplest API requests require only a GET to the endpoint URL:

.. code-block:: none

    $ curl -i https://api.pub.build.mozilla.org/versions

In many cases, arguments are included in the URL path or as query arguments, as described in the endpoint documentation.
For request methods that include a request body, the body should be formatted as a JSON object or array, as described by the documentation.
In this case, the Content-Type header must also be set properly.
For example:

.. code-block:: none

    $ curl --data-ascii '{"description": "new token", "permissions": ["base.tokens.issue"]}' \
        -H 'Content-Type: application/json'
        -H 'Authorization Bearer your.token.here'
        http://api.pub.build.mozilla.org/tokenauth/tokens

API Responses
-------------

Response status is indicated via HTTP status codes.
Where certain codes have additional meaning, that is described in the documentation for the endpoint.

A successful (2xx) response body contains a JSON object with a ``result`` key containing the result data.
Other top-level response keys may be added during development of the API.

.. code-block:: none

    $ curl -i https://api.pub.build.mozilla.org/versions
    HTTP/1.1 200 OK
    Date: Tue, 16 Dec 2014 17:09:46 GMT
    Server: Apache
    X-Backend-Server: web1.releng.webapp.scl3.mozilla.com
    Content-Length: 4751
    Vary: Accept-Encoding
    Content-Type: application/json

    {
      "result": {
        "blueprints": {
          "auth": {
            "distribution": "relengapi",
            "version": "1.0.1"
          },
          # ..
        },
        "distributions": {
          "amqp": {
            "project_name": "amqp",
            "version": "1.4.6"
          },
          # ..
        }
      }
    }

An error (4xx or 5xx) response will contain an ``error`` object with keys ``code``, ``description``, and ``name`` describing the error:


.. code-block:: none

    $ curl -i https://api.pub.build.mozilla.org/foo/bar
    HTTP/1.1 404 NOT FOUND
    Date: Tue, 16 Dec 2014 17:16:25 GMT
    Server: Apache
    X-Backend-Server: web2.releng.webapp.scl3.mozilla.com
    Content-Length: 205
    Vary: Accept-Encoding
    Content-Type: application/json

    {
      "error": {
        "code": 404,
        "description": "The requested URL was not found on the server.  If you entered the URL manually please check your spelling and try again.",
       "name": "Not Found"
      }
    }

For internal server errors, if debug mode is enabled, then the ``error`` object will also contain a ``traceback`` giving the failing Python traceback.


