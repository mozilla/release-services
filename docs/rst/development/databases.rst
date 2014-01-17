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

TBD
