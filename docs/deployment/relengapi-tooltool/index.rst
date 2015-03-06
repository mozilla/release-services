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
