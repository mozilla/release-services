Deploying Tooltool
==================

Tooltool requires an AWS configuration, which it uses to sign URLs for uploads and downloads.
Aside from that, it requires a set of buckets, one in each region, in which to store the uploaded files.
These buckets should already exist, and access should be limited to the AWS IAM role corresponding to the AWS credentials.

Specify the regions and buckets like this::

    TOOLTOOL_REGIONS = {
        'us-east-1': 'my-tooltool-bucket-us-east-1',
        'us-west-1': 'my-tooltool-bucket-us-west-1',
    }

Permissions
-----------

Tooltool defines two visibility levels:

 * ``public`` -- distribution is not limited
 * ``internal`` -- for Mozilla employees only

These correspond to the eponymous Mozilla data security levels.

The following permissions control whether users can upload or download files at each visibility level:

 * ``tooltool.download.public``
 * ``tooltool.download.internal``
 * ``tooltool.upload.public``
 * ``tooltool.upload.internal``

Note that the ``internal`` permissions do not imply the ``public`` permissions.

To allow any user (even unauthenticated) to download public files, set ``TOOLTOOL_ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD = True``.
