AWS
===

RelengAPI interfaces with AWS via `boto <http://boto.readthedocs.org/>`_.
Boto supports a number of ways to get its access credentials, including its own configuration files and the AWS instance data (from the IAM role assigned to the instance).
If you prefer to supply credentials directly in the RelengAPI configuration, do so like this:

.. code-block:: none

    AWS = {
        'access_key_id': 'access',
        'secret_access_key': 'secret',
    }

