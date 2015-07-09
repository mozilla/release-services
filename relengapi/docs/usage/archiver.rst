Archiver
========

Archiver simply takes repository archive urls and returns an s3 location for the same archive, while submitting the
archive to s3 if it doesn't already exist. 

If the archive exists, the response will redirect with a 302 and location for the s3 url equivalent.

If the archive does not already exist in s3, the response will accept the request (202) and return the task location url
that is monitoring the current state of creating and uploading the archive to s3.

Currently, only hg.mozilla.org support is configured:
    ARCHIVER_HGMO_URL_TEMPLATE = "https://hg.mozilla.org/{repo}/archive/{rev}.{suffix}/{subdir}"


Examples::

    # To get an in-tree Mozharness archive based on: http://hg.mozilla.org/projects/ash/rev/42bf8560b395
    > curl -i http://127.0.0.1:8010/archiver/hgmo/projects/ash/42bf8560b395?subdir=testing/mozharness&preferred_region=us-west-2
    HTTP/1.0 202 ACCEPTED
    Content-Type: application/json
    Content-Length: 18
    Location: http://127.0.0.1:8010/archiver/status/projects_ash-42bf8560b395.tar.gz_testing_mozharness
    Server: Werkzeug/0.10.4 Python/2.7.6
    Date: Fri, 19 Jun 2015 22:41:29 GMT

    {
      "result": {}
    }%

    # In the above example, the s3 archive does not exist so Archiver will create it. poll the Location header url in the above response to monitor state
    > curl -i http://127.0.0.1:8010/archiver/status/projects_ash-42bf8560b395.tar.gz_testing_mozharness
    HTTP/1.0 200 OK
    Content-Type: application/json
    Content-Length: 683
    Server: Werkzeug/0.10.4 Python/2.7.6
    Date: Fri, 19 Jun 2015 22:41:41 GMT

    {
      "result": {
        "s3_urls": {
          "us-east-1": "https://archiver-us-east-1.s3.amazonaws.com/projects/ash-42bf8560b395.tar.gz/testing/mozharness?Signature=0f%2FvcSqbUylTWgwx8yYYISO6%2FJM%3D&Expires=1434753993&AWSAccessKeyId=AKIAIYHUTJ7BG2GMUTXA",
          "us-west-2": "https://archiver-us-west-2.s3-us-west-2.amazonaws.com/projects/ash-42bf8560b395.tar.gz/testing/mozharness?Signature=i6%2B9d4r8u8YuUNTmT4kX9jcaNrA%3D&Expires=1434753992&AWSAccessKeyId=AKIAIYHUTJ7BG2GMUTXA"
        },
        "src_url": "https://hg.mozilla.org/projects/ash/archive/42bf8560b395.tar.gz/testing/mozharness",
        "state": "SUCCESS",
        "status": "Task completed! Check 's3_urls' for upload locations."
      }
    }%

    # We can see above that Archiver has created two s3 archives across two regions. We can use those urls to grab the archive.
    # Subsequent requests of the original endpoint also just redirects the s3 location
    > curl -i http://127.0.0.1:8010/archiver/hgmo/projects/ash/42bf8560b395?subdir=testing/mozharness&preferred_region=us-west-2
    HTTP/1.0 302 FOUND
    Content-Type: text/html; charset=utf-8
    Content-Length: 625
    Location: https://archiver-us-west-2.s3-us-west-2.amazonaws.com/projects/ash-42bf8560b395.tar.gz/testing/mozharness?Signature=oZVrvFhkM6RR8rxKryt9vTWmvTQ%3D&Expires=1434754032&AWSAccessKeyId=AKIAIYHUTJ7BG2GMUTXA
    Server: Werkzeug/0.10.4 Python/2.7.6
    Date: Fri, 19 Jun 2015 22:42:12 GMT

    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
    <title>Redirecting...</title>
    <h1>Redirecting...</h1>
    <p>You should be redirected automatically to target URL: <a href="https://archiver-us-west-2.s3-us-west-2.amazonaws.com/projects/ash-42bf8560b395.tar.gz/testing/mozharness?Signature=oZVrvFhkM6RR8rxKryt9vTWmvTQ%3D&amp;Expires=1434754032&amp;AWSAccessKeyId=AKIAIYHUTJ7BG2GMUTXA">https://archiver-us-west-2.s3-us-west-2.amazonaws.com/projects/ash-42bf8560b395.tar.gz/testing/mozharness?Signature=oZVrvFhkM6RR8rxKryt9vTWmvTQ%3D&amp;Expires=1434754032&amp;AWSAccessKeyId=AKIAIYHUTJ7BG2GMUTXA</a>.  If not click the link.%


Types
-----

.. api:autotype:: MozharnessArchiveTask

Endpoints
---------

.. api:autoendpoint:: archiver.*

