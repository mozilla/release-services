Using Tooltool
==============

In most cases, you will use tooltool with the [tooltool client](https://github.com/mozilla/build-tooltool/blob/master/tooltool.py).
Just give it the right URL and you should be on your way.

Endpoints
---------

.. api:endpoint:: tooltool.get
        GET /tooltool/sha512/<hash>

    :param hash: SHA512 hash of the desired file

    This endpoint returns a 302 response with a Location header containing the URL at which the desired file can be downloaded.
    The URL may contain authentication information -- avoid logging it if possible.
    The URL may also expire a short time after it is issued, so it should be used immediately.
