Using Celery Tasks
==================

Releng API uses `Celery <http://www.celeryproject.org/>`_ to distribute tasks to workers.

The implementation of tasks within Releng API is very close to that documented for Celery itself, with only a few minor differences.

Defining Tasks
--------------

Tasks are defined in blueprints using a decorator from ``relengapi.lib.celery``, rather than that suggested by the Celery documentation::

    from relengapi.lib import celery

    @celery.task
    def add(x, y, z):
        return x + y + z

Other than using a different decorator, everything else remains the same.
You can also pass options, just as for Celery's ``task`` decorator::

    @celery.task(serializer='json')
    def add(x, y, z):
        return x + y + z

Each task will run in an application context, so the application is available at ``flask.current_app``.

Invoking Tasks
--------------

Invoke a task using exactly the same syntax as suggested in the Celery documentation.
This must be done from within a Flask application context (most commonly, in a request). ::

    def get_sum(x, y, z):
        add.delay(x, y, z).get()
