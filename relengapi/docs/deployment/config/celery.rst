Celery
======

Celery is used to run tasks outside of HTTP requests, including periodic tasks (badpenny).
In order to use Celery to run any tasks, you will need to set ``CELERY_BROKER_URL`` and ``CELERY_BACKEND``:

.. code-block:: none

    CELERY_BROKER_URL='amqp://'
    CELERY_BACKEND='amqp'

Celery currently defaults to using pickle to serialize messages, yet complains that this is deprecated.
To avoid these warnings, use JSON instead:

.. code-block:: none

    CELERY_ACCEPT_CONTENT=['json']
    CELERY_TASK_SERIALIZER='json'
    CELERY_RESULT_SERIALIZER='json'

Finally, by default Celery limits logging to the WARNING level.
To see more output from RelengAPI, without the additional verbose output from Celery itself, set ``RELENGAPI_CELERY_LOG_LEVEL`` to the desired level:

.. code-block:: none

    RELENGAPI_CELERY_LOG_LEVEL = 'DEBUG'


