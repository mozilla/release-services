Deploying Archiver
==================

Archiver requires a separate configuration for each endpoint. Within these endpoint configs, you need to state the s3
buckets, where each bucket represents a region and the template url that will be formatted by query params passed to
the endpoint.

For AWS credentials, each bucket should be limited to the AWS IAM role corresponding to the AWS credentials. Buckets in
the configuration are required to be pre-existing.

Archiver also uses a db for tracking celery tasks in order not to create duplicates.
Like other parts of relengapi that have a db component, you must supply a sqlalchemy uri.

Finally, Archiver uses Celery. You will need to provide a broker and back-end.

Example config::

    SQLALCHEMY_DATABASE_URIS = {
       'relengapi': 'sqlite:////tmp/relengapi.db',
    }

    # using rabbitmq locally in a staging setup
    CELERY_BROKER_URL='amqp://guest@localhost//'
    CELERY_BACKEND='amqp'

    AWS = {
        'access_key_id': 'accessKeyExample',
        'secret_access_key': 'secretAccessKeyExample',
    }

    ARCHIVER_S3_BUCKETS = {
        'us-east-1': 'archiver-us-east-1',
        'us-west-2': 'archiver-us-west-2'
    }

    ARCHIVER_HGMO_URL_TEMPLATE = "https://hg.mozilla.org/{repo}/archive/{rev}.{suffix}/{subdir}"
