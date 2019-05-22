# -*- coding: utf-8 -*-
from google.cloud import storage as gcp_storage
from google.oauth2.service_account import Credentials


def get_bucket(service_account):
    '''
    Build a Google Cloud Storage client & bucket
    from Taskcluster secret
    '''
    assert isinstance(service_account, dict)

    # Load credentials from Taskcluster secret
    if 'bucket' not in service_account:
        raise KeyError('Missing bucket in GOOGLE_CLOUD_STORAGE')
    bucket = service_account.pop('bucket')

    # Use those credentials to create a Storage client
    # The project is needed to avoid checking env variables and crashing
    creds = Credentials.from_service_account_info(service_account)
    client = gcp_storage.Client(project=creds.project_id, credentials=creds)

    return client.get_bucket(bucket)
