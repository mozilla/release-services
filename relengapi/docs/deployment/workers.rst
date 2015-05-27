Celery Workers
==============

Releng API uses `Celery <http://www.celeryproject.org/>`_ to distribute tasks to workers.
Releng API workers are simply Celery workers invoked with ::

    celery -A relengapi worker

On a system or Python virtualenv where relengapi are installed.
The ``RELENGAPI_SETTINGS`` environment variable must be set correctly.
