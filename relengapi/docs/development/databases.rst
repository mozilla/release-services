Using Databases
===============

Releng API uses `SQLAlchemy Core <http://sqlalchemy.org/>`_ to access databases.
Releng API does not use the SQLAlchemy ORM.

The system supports multiple, independent databases, each identified by a short name.
Of course, it's impossible to perform joins between independent databases.
The base defines one, ``relengapi``, that should serve as the default location for new tables.
Blueprints can define other databases, or add tables to existing databases.

The same database access object is available at ``current_app.db`` and ``g.db``; callers can use whichever is easier.

Users configure the SQLAlchemy database URIs using the ``SQLALCHEMY_DATABASE_URIS`` configuration parameter, which is a dictionary mapping database names to URLs.

Adding Tables
-------------

RelengAPI supports SQLAlchemy's declarative mapping syntax, with a small twist to support multiple databases:
instead of calling ``sqlalchemy.ext.declarative.declarative_base()`` to get a base class, call ``relengapi.db.declarative_base(dbname)``.

For example::

    from relengapi.lib import db

    class User(db.declarative_base('relengapi')):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        name = Column(String(100))
        password = Column(String(100))

The set of databases that a Releng API instance knows about is based on the tables it knows about in all installed blueprints.
So adding a new database is as simple as creating some tables with ``db.declarative_base('my_new_db_name')``.

With this in place, and with an entry for ``my_new_db_name`` in the user's ``settings.py`` file, ``relengapi createdb`` will create the tables automatically.

Many-to-Many Relationships
--------------------------

The `SQLAlchemy Documentation <http://docs.sqlalchemy.org/en/rel_0_9/orm/relationships.html#many-to-many>`_ describes most of the details of setting up many-to-many relationships.
In RelengAPI, the metadata for the association table needs to be fetched from the declarative base:

.. code-block:: none

    allocations = Table(
        'allocations', db.declarative_base('jacuzzi_allocator').metadata,
        ...
    )

The linked tables are defined as described above.


Using Tables
------------

Use of the ORM layer requires a session.
The session is available from ``g.db.session(dbname)``, given the database name.
For example::

    @bp.route('/add/foo')
    def add_foo():
        session = g.db.session('relengapi')

        u = User()
        u.name = 'Foo'
        u.password = 'sekrit'
        session.add(u)
        session.commit()

        return 'ok'

As you might expect, bad things will happen if you try to use tables from one database with a session for another database.

As a shortcut, each table object has a ``query`` property which is automatically bound to the table and session; this is similar to the property provided by Flask-SQLAlchemy::

    @bp.route('/get/foo')
    def get_foo():
        u = User.query.filter_by(name='Foo').first()
        return jsonify(userid=u.id)

Unique Row Support (Get or Create)
----------------------------------

RelengAPI also supports a way to get a unique row from a table, if the row doesn't exist it will create the row for you.

.. warning:: This does not protect against race conditions in other webheads or sessions, which can occur from the moment you call invoke up until you commit your DB session. These will usually raise an SQLAlchemy ``IntegrityError`` if there is a failure.

First you make your ORM Table inherit from ``UniqueMixin``::

    from relengapi.lib import db

    class MyTable(db.declarative_base(...), db.UniqueMixin):
        __tablename__ = "mytable"
        id = Column(Integer, primary_key=True)
        name = Column(String(100), unique=True, nullable=False)
        other_stuff = Column(String(100))

        @classmethod
        def unique_hash(cls, name, *args, **kwargs):
            return name

        @classmethod
        def unique_filter(cls, query, name, *args, **kwargs):
            return query.filter(Uniqueness_Table.name == name)

There are a few things going on here, first you're defining your table, as you do with any other ORM.

Then you define a classmethod hash (``unique_hash``) that accepts all the agrs you might want to use to also create. The return value here is your hash, which can be a tuple or a scalar value, and must be guaranteed unique for the row.

Next you define a classmethod filter (``unique_filter``) which is used to filter the table rows down to what matters. The first argument is always ```query``` which is the sqlalchemy query we're using. Following args are always up to you.

Usage is quite simple with one caveat, you need to pass the DB session through each time::

    foo = MyTable.as_unique(session, name='unique_name', other="foo")

The above would return a row from ``MyTable`` with ``name='unique_name'`` if it exists, if not it would create said row, putting in ``'foo'`` as the value for the ``other`` column.

.. note:: If the row existed, and the other column contained different data than foo (e.g. ``'bar'``) the value returned would have 'bar' as the ``other`` column, this code does not assume you'd want to update the existing row, merely get it.


Engines, MetaData, etc.
-----------------------

Although most uses of the database should occur by the ORM methods described above, some operations require more data.

The engine for a database is available from the ``current_app.db.engine(dbname)`` method::

    eng = current_app.db.engine('relengapi')

The list of database names is at ``current_app.db.database_names``.

The known metadata for each database is in ``current_app.db.metadata``, keyed by database name.

Interactive Use
---------------

It can sometimes be useful to "live" ORM operations at an interactive prompt.
The ``relengapi repl`` command will run a read-eval-print loop with an active RelengAPI app:

.. code-block:: none

    $ relengapi repl
    2015-04-08 15:20:16,642 registering blueprint badpenny
    2015-04-08 15:20:16,644 registering blueprint base
    2015-04-08 15:20:16,645 registering blueprint tokenauth
    2015-04-08 15:20:16,646 registering blueprint auth
    2015-04-08 15:20:16,647 registering blueprint docs
    'app' is the current application.
    Python 2.7.9 (default, Feb 22 2015, 12:26:28)
    [GCC 4.8.3] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    (InteractiveConsole)
    >>> s = app.db.session('relengapi')

Alternative Column types
------------------------

Relengapi provides some custom Column types that can be used in SQL Models.

These can be used like any other column in SQLAlchemy ORMs::

    from relengapi.db import SomeColumn
    class Widget(db.declarative_base('...')):
        someField = sa.Column(SomeColumn, ...)

UTCDateTime Column
..................

A DateTime column where values are always stored and retrieved in UTC. Specifically
the datetime objects returned are always timezone aware (with pytz.UTC set). On
inserts into the table it automatically converts the object to UTC when a timezone
aware datetime object is passed in.

example::

    from relengapi.lib import db
    import sqlalchemy as sa
    
    class Log(db.declarative_base('...')):
        __tablename__ = 'logs'
        id = sa.Column(sa.Integer, primary_key=True)
        dt = sa.Column(db.UTCDateTime,
                       default=datetime.datetime.utcnow,
                       nullable=False)
        msg = sa.Column(sa.String(255), nullable=False)
