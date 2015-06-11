Archiver
========

Archiver simply takes repository archive urls and returns an s3 location for the same archive, while submitting the
archive to s3 if it doesn't already exist. 


If the archive exists, the response will redirect with a 302 and location for the s3 url equivalent.

If the archive does not already exist in s3, the response will accept the request (202) and return the task location url
that is monitoring the current state of creating and uploading the archive to s3.

Currently, only Mozharness is configured:
    "URL_SRC_TEMPLATE": "https://hg.mozilla.org/{repo}/archive/{rev}.{suffix}/testing/mozharness"



Examples::

    # To get an in-tree Mozharness archive based on: http://hg.mozilla.org/mozilla-central/rev/3d11cb4f31b9 
    > curl -i http://127.0.0.1:8010/archiver/mozharness/3d11cb4f31b9\?repo\=mozilla-central\&region\=us-east-1
    HTTP/1.0 202 ACCEPTED
    Content-Type: application/json
    Content-Length: 18
    Location: http://127.0.0.1:8010/archiver/status/3d11cb4f31b9
    Server: Werkzeug/0.10.4 Python/2.7.6
    Date: Tue, 09 Jun 2015 22:19:15 GMT

    {
      "result": {}
    }


    # In the above example, the s3 archive does not exist so Archiver will create it. poll the Location header url in the above response to monitor state
    > curl -i http://127.0.0.1:8010/archiver/status/3d11cb4f31b9
    HTTP/1.0 200 OK
    Content-Type: application/json
    Content-Length: 682
    Server: Werkzeug/0.10.4 Python/2.7.6
    Date: Tue, 09 Jun 2015 22:19:24 GMT

    {
      "result": {
        "s3_urls": {
          "us-east-1": "https://archiver-mozharness-us-east-1.s3.amazonaws.com/mozilla-central-3d11cb4f31b9.tar.gz?Signature=GB%2F%2Feye%2Fidj7BrOYEZQNHSFSNyY%3D&Expires=1433888658&AWSAccessKeyId=AKIAIYHUTJ7BG2GMUTXA",
          "us-west-2": "https://archiver-mozharness-us-west-2.s3-us-west-2.amazonaws.com/mozilla-central-3d11cb4f31b9.tar.gz?Signature=7%2FnVzYSgGAs8lVP9x%2FvkI%2FklDls%3D&Expires=1433888659&AWSAccessKeyId=AKIAIYHUTJ7BG2GMUTXA"
        },
        "src_url": "https://hg.mozilla.org/mozilla-central/archive/3d11cb4f31b9.tar.gz/testing/mozharness",
        "state": "SUCCESS",
        "status": "Task completed! Check 's3_urls' for upload locations."
      }
    }


    # We can see above that Archiver has created two s3 archives across two regions. We can use those urls to grab the archive.
    # Subsequent requests of the original endpoint also just redirects the s3 location
    > curl -i http://127.0.0.1:8010/archiver/mozharness/3d11cb4f31b9\?repo\=mozilla-central\&region\=us-east-1
    HTTP/1.0 302 FOUND
    Content-Type: text/html; charset=utf-8
    Content-Length: 599
    Location: https://archiver-mozharness-us-east-1.s3.amazonaws.com/mozilla-central-3d11cb4f31b9.tar.gz?Signature=094S3haXO5LMbFtCObyh8FhN%2FD0%3D&Expires=1433888697&AWSAccessKeyId=AKIAIYHUTJ7BG2GMUTXA
    Server: Werkzeug/0.10.4 Python/2.7.6
    Date: Tue, 09 Jun 2015 22:19:57 GMT

    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
    <title>Redirecting...</title>
    <h1>Redirecting...</h1>
    <p>You should be redirected automatically to target URL: <a href="https://archiver-mozharness-us-east-1.s3.amazonaws.com/mozilla-central-3d11cb4f31b9.tar.gz?Signature=094S3haXO5LMbFtCObyh8FhN%2FD0%3D&amp;Expires=1433888697&amp;AWSAccessKeyId=AKIAIYHUTJ7BG2GMUTXA">https://archiver-mozharness-us-east-1.s3.amazonaws.com/mozilla-central-3d11cb4f31b9.tar.gz?Signature=094S3haXO5LMbFtCObyh8FhN%2FD0%3D&amp;Expires=1433888697&amp;AWSAccessKeyId=AKIAIYHUTJ7BG2GMUTXA</a>.  If not click the link.



Types
-----

.. api:autotype:: MozharnessArchiveTask

Endpoints
---------

.. api:autoendpoint:: archiver.*

