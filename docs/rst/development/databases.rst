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

To add tables, define them just like you would an ``sqlalchemy.Table``, but use ``db.Table`` instead.
As a tablename, pass a colon-separated string containing the database name and table name, e.g.,  ``relengapi:users``.
Do not pass a metadata instance.
For example:

    from relengapi import db
    users = db.Table('relengapi:users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(100)),
        sa.Column('passowrd', sa.String(100)),  # cleartext, of course! ;)
    )

Using Tables
------------

Now, in an application context (for example, in a request), you can either use a global variable defined as above:

    @bp.route('/users')
    def users():
        conn = g.db.connection('relengapi')
        r = conn.execute(users.select()).fetchall()
        ...

Or, if the table isn't in scope, fetch it from ``g.db.tables``, which is indexed both by colon-separated names and as a two-level dictionary::

    tbl = g.db.tables['relengapi:users']
    tbl = g.db.tables['relengapi']['users']

In either case, you'll need a connection to the the selected database.
You can get that from ``g.db.connect(dbname)``, as illustrated above.
