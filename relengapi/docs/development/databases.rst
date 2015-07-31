Using Databases
===============

RelengAPI uses `SQLAlchemy Core <http://sqlalchemy.org/>`_ to access databases.

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

Changing Schema
---------------

RelengAPI uses `Alembic <https://alembic.readthedocs.org/>`_ to manage schema changes, such as adding tables or altering column types.
Alembic provides a framework to support smooth upgrades and downgrades of the production database without downtime.
However, it still requires careful thought and attention to design such upgrades!

In production, RelengAPI has a MySQL backend, so migrations target MySQL.
Unfortunately, SQLite, which is used by default in development environments, does not have very good support for schema modification.
As a result, many schema migrations will not run correctly on SQLite, although ``relengapi createdb`` will.
If you are developing a schema change, please set up a MySQL environment so support your testing.
It may also help to include ``SQLALCHEMY_DB_LOG = True`` in your settings to see the DDL statements Alembic and SQLAlchemy are generating.

Running Alembic
...............

The ``relengapi alembic`` command wraps most ``alembic`` commands, adding a database name.
For example, where the Alembic documentation suggests running ``alembic stamp``, you might instead run ``relengapi alembic relengapi stamp``, where the second ``relengapi`` indicates the database to which you wish to apply the stamp operation.

Writing A Migration
...................

To make a change to the database, first make the change in your Python model.
For the sake of example, we'll add a ``comment`` field to the ``auth_tokens`` table in the ``relengapi`` database:

.. code-block:: diff


    diff --git a/relengapi/blueprints/tokenauth/tables.py b/relengapi/blueprints/tokenauth/tables.py
    index ef51a66..f53f0fc 100644
    --- a/relengapi/blueprints/tokenauth/tables.py
    +++ b/relengapi/blueprints/tokenauth/tables.py
    @@ -21,4 +21,5 @@ class Token(db.declarative_base('relengapi')):
         typ = sa.Column(sa.String(4), nullable=False)
         description = sa.Column(sa.Text, nullable=False)
    +    comment = sa.Column(sa.Text, nullable=False)
         user = sa.Column(sa.Text, nullable=True)
         disabled = sa.Column(sa.Boolean, nullable=False)

Next, create a migration using ``revision`` with ``--autogenerate``.


.. code-block:: none

    relengapi alembic relengapi revision -m "add auth_tokens.comment" --autogenerate

This consults the live database, comparing it to the SQLAlchemy model.
It produces a new migration file tagged with a short hexadecimal revision ID, and provides the filename to you.
Open that file in your editor to fine-tune it.

.. note::

    If you have multiple RelengAPI databases configured with the same SQLAlchemy URL in your settings file, Alembic may add unexpected ``op.drop_table`` invocations.
    Simply delete these from the generated migration file.

The result for this example looks like this:

.. code-block:: none

    # revision identifiers, used by Alembic.
    revision = '175160eab61f'
    down_revision = '2de009660da3'
    branch_labels = None
    depends_on = None


    def upgrade():
        op.add_column('auth_tokens', sa.Column('comment', sa.Text(), nullable=False))


    def downgrade():
        op.drop_column('auth_tokens', 'comment')

Try out the upgrade:

.. code-block:: none

    relengapi alembic relengapi upgrade

And try out the downgrade:

.. code-block:: none

    relengapi alembic relengapi downgrade

Then re-upgrade and update the code to use the new schema.
Commit the migration file right alongside the code changes.

When you create a pull request, the ``validate.sh`` script will automatically run your upgrade and downgrade and verify that they result in the expected schemas.

Non-Compatible Migrations
.........................

It's impossible to deploy new code and a schema migration at exactly the same time.
If a migration will make existing code fail, then applying that migration will cause an outage.
Thankfully, most migrations involve adding tables or columns.
Adding a table is always safe, unless there are no inter-table consistency checks.
Adding a column is generally safe, as long as it has a default or allows NULL so that insert operations not mentioning the column do not fail.
In general, it's best to test your schema migration's compatibility by hand: apply the upgrade, then check out the pre-upgrade code, run it, and verify that all of the possibly-affected operations still work.

If you must make an incompatible change, you may need to perform several deployments of code and schema changes.
In general, you will need to either deploy an intermediate schema which is compatible with both old and new code, or deploy an intermediate code revision which is compatible with both old and new schemas.

Let's take the example of changing a column from an integer to a string.
There's no good in-between schema, so we'll create an in-between code revision

#. Add code to handle inserts, updates, and queries where the column is a string.
   This can be a simple as adding a try/except that retries with a string when an integer fails.
   Deploy this code.
#. Deploy the schema upgrade.
#. Update the code to assume strings, removing support for integers.
   Deploy this code.

If you are proposing a non-compatible migration, it's best to submit the whole process as a series of pull requests, with each step clearly described.

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

.. note::

    If the row existed, and the other column contained different data than foo (e.g. ``'bar'``) the value returned would have 'bar' as the ``other`` column, this code does not assume you'd want to update the existing row, merely get it.


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
