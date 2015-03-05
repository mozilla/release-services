Using Tooltool
==============

In most cases, you will use tooltool with the [tooltool client](https://github.com/mozilla/build-tooltool/blob/master/tooltool.py).
Just give it the right URL and you should be on your way.

Types
-----

.. api:autotype:: File UploadBatch

Endpoints
---------

.. api:autoendpoint:: tooltool.*

.. api:endpoint:: tooltool.legacy_get
    GET /tooltool/sha512/<hash>

    :param hash: SHA512 hash of the desired file
    :response: 302 redirect to a signed URL, or 404 or 403

    This endpoint returns a 302 response with a Location header containing the URL at which the desired file can be downloaded.
    The URL may contain authentication information -- avoid logging it if possible.
    The URL may also expire a short time after it is issued, so it should be used immediately.
