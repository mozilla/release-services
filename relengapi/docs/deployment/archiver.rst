Deploying Archiver
==================

Archiver requires a separate configuration for each endpoint. Within these endpoint configs, you need to state the s3
buckets, where each bucket represents a region and the template url that will be formatted by query params passed to
the endpoint.

For AWS credentials, each bucket should be limited to the AWS IAM role corresponding to the AWS credentials. Buckets in
the configuration are required to be pre-existing.

Finally, Archiver avails of Celery. You will need to provide a broker and back-end.

Example config::

    # using rabbitmq locally in a staging setup
    CELERY_BROKER_URL='amqp://guest@localhost//'
    CELERY_BACKEND='amqp'

    AWS = {
        'access_key_id': 'accessKeyExample',
        'secret_access_key': 'secretAccessKeyExample',
    }

    # for the mozharness endpoint
    SUBREPO_MOZHARNESS_CFG = {
        'S3_BUCKETS': [
            {'REGION': 'us-east-1', 'NAME': 'example-bucket-name-for-us-east-1'},
            {'REGION': 'us-west-2', 'NAME': 'example-bucket-name-for-us-west-2'}
        ],
        "URL_SRC_TEMPLATE": "https://hg.mozilla.org/{repo}/archive/{rev}.{suffix}/testing/mozharness"
    }
