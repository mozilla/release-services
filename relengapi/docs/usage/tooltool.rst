Tooltool
========

In most cases, you will use tooltool with the [tooltool client](https://github.com/mozilla/build-tooltool/blob/master/tooltool.py).
Just give it the right base URL and manifest and you should be on your way.

If you need more control, the API details are below.

Periodic Tasks
--------------

When a user uploads a file to tooltool, the file is transferred directly to Amazon S3.
This occurs via a "signed URL" which temporarily grants the user write access to the file.

There is a periodic task named ``relengapi.blueprints.tooltool.grooming.check_pending_uploads`` which runs every 10 minutes.
It verifies any newly uploaded files and records their presence for subsequent download.
Uploads can only be verified after the signed URL has expired -- otherwise they could be changed after the fact!

Separately from verifying uploads, a task named ``relengapi.blueprints.tooltool.grooming.replicate`` runs every hour to replicate content between AWS regions.
Any files which are not in at least one, but not all configured AWS regions are copied to the remaining regions.
Once the copies are complete, they become available to clients for download.

Thus there is a short period after a file is uploaded where it is available in zero, and then only one, region.

Types
-----

.. api:autotype:: File UploadBatch

Endpoints
---------

.. api:autoendpoint:: tooltool.*
