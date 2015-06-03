Authentication
==============

API requests can be made via any authentication mechanism that provides the required permissions.

No Authentication
-----------------

Many endpoints provide public data.
These endpoints can be accessed without any authentication at all.

Cookie Authentication
---------------------

If a proper session cookie is included with the request, then the API request is carried out in the context of that session.
This is most often used for requests made from the RelengAPI UI.
Automated users of RelengAPI should not use cookies.

Token Authentication
--------------------

As shown in the POST example above, a request containing a bearer token in the ``Authorization`` header is carried out in the context of the permissions associated with the token.
See :doc:`tokenauth` for more information on token authentication.


