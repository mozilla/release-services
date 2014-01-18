Using Databases
===============

Releng API uses `SQLAlchemy Core <http://sqlalchemy.org/>`_ to access databases.
Releng API does not use the SQLAlchemy ORM.

The system supports multiple, independent databases, each identified by a short name.
Of course, it's impossible to perform joins between independent databases.
The base defines one, 'relengapi', that should serve as the default location for new tables.
Blueprints can define other databases, or add tables to existing databases.

Users configure the SQLAlchemy database URIs using the ``SQLALCHEMY_DATABASE_URIS`` configuration parameter, which is a dictionary mapping database names to URLs.

Adding Tables
-------------

To add tables, write a method in the blueprint that creates the Table objects, and register it with ``releng.db``::

    from relengapi import db
    @db.register_model(bp, 'mydatabase')
    def model(metadata):
        sa.Table('widgets', metadata,
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('model', sa.Integer),
            sa.Column('manufacture_date', sa.Integer, nullable=False),
            sa.Column('serial', sa.String(100), nullable=False),
        )
        sa.Table('models', metadata,
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('name', sa.String(100)),
        )

The arguments to ``register_model`` are the blueprint object and the name of the database containing the tables.
To add tables to several database, repeat this process for each database.

Note that the Table objects will be instantiated once per app.
Do *not* treat them as module-global variables.
