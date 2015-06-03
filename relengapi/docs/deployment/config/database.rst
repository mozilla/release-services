Databases
=========

Releng API, as a kind of glue, generally connects to a numnber of databases.
Each database has a short name, and requires that a longer SQLAlchemy URL be configured for it.

This is done in the ``SQLALCHEMY_DATABASE_URIS`` configuration, which is a dictionary mapping names to URIs.
If this configuration key is not present, then RelengAPI will create SQLite databases in the root of the source directory.
This is effective for development, but certainly not for production.

The database for the relengapi core is named ``relengapi``.
Other blueprints may require additional URIs.

If you ever need to see what SQLAlchemy is doing with the connection pool, it is useful to enable verbose query logging.
To do so, set ``SQLALCHEMY_DB_LOG = True``.
Note that this output is *very* verbose and may severely impact site performance.
