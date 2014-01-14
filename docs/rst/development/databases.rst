Using Databases
===============

Releng API uses `Flask-SQLAlchemy <http://pythonhosted.org/Flask-SQLAlchemy/>`_ to access databases, so in general the documentation for that extension applies.

Base Tables
-----------

To use a table defined in the Releng API base from a view function, simply import the module that contains it and use ordinary SQLAlchemy syntax.
For example::

    from relengapi.models import base
    def users():
        users = base.Users.query.all()
        return jsonify(users)

The base models are all defined in Python modules under ``relengapi.models``, one per database.
The corresponding files are in ``base/relengapi/models``.
Consult those files for the specific tables that are available.

Adding Tables
-------------

WARNING: Flask-SQLAlchemy requires that tables have unique names across all databases.

Tables that might conceivably be used by multiple blueprints should be included in the Releng API base.
Add a new declarative table class to the appropriate module, most likely ``base/relengapi/models/base.py``.

Tables that specific to a blueprint can be defined in the blueprint itself.
For example, the Kron blueprint's task list is of no use to any other blueprint.
It should be defined in a module named after the blueprint, under ``relengapi.models``, and all defined tables should be prefixed with the blueprint name.
For Kron, that might look like this::

    from relengapi import db

    class KronTasks(db.Model):
        id = db.Column(...)
        ...

Adding Databases
----------------

Flask-SQLAlchemy supports accessing multiple databases from a single app.
Within the Releng API, this is used to connect to databases shared with other applications such as Buildbot.
Such secondary databases are always added to the Releng API base.

Note that individual blueprints should not necessarily have dedicated databases; see "Adding Tables" above.
That may occasionally be required while migrating applications into the Releng API, but should only be done temporarily.

To add a new database:

 * Add a new Python module to ``base/relengapi/models``
 * Add documentation about configuring the database to ``docs/rst/deployment/config.rst``
 * Add configuration to your own settings

In the model module, set ``__bind_key__`` to the bind name for the database in each table class.
For example::

    class SomeTable(db.Model):
        __bind_key__ = 'newdatabase'

