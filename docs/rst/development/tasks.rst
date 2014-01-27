Using Tasks
===========

Releng API uses `Celery <http://www.celeryproject.org/>`_ to distribute tasks to workers.

The implementation of tasks within Releng API is very close to that documented for Celery itself, with only a few minor differences.

Defining Tasks
--------------

Tasks are defined in blueprints with a *slightly* different decorator than that suggested by the Celery documentation:

    from relengapi import celery
    bp = Blueprint('myblueprint', __name__)

    @celery.task(bp)
    def add(x, y, z):
        return x + y + z

You can also pass options, just as for Celery's ``task`` decorator:

    @celery.task(bp, serializer='json')
    def add(x, y, z):
        return x + y + z

Each task will run in an application context, so the application is available at ``flask.current_app``.

Invoking Tasks
--------------

Invoke a task using exactly the same syntax as suggested in the Celery documentation.
This must be done from within a Flask application context (most commonly, in a request).

    def get_sum(x, y, z):
        add.delay(x, y, z).get()
