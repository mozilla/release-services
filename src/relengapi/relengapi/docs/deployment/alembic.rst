Database Migrations
===================

Database migrations are handled through alembic through the command line tool ``relengapi alembic``.
This tool is built based on Flask-Migrate_, and its usage is roughly one to one.

Manual management of the database without the relengapi tool can be done through alembic itself, by
specifying the configuration file i.e. ``alembic -c relengapi/alembic/*/alembic.ini``.

Command Reference
-----------------

``relengapi alembic --help``
    Shows a list of available commands.


``relengapi alembic DBNAME init``
    Initializes migration support for the particular database.

``relengapi alebic DBNAME revision [--message MESSAGE] [--autogenerate] [--sql] [--head HEAD] [--splice] [--branch-label BRANCH_LABEL] [--version-path VERSION_PATH] [--rev-id REV_ID]``
    Creates an empty revision script. The script needs to be edited manually with the upgrade and
    downgrade changes. See Alembic’s documentation for instructions on how to write migration scripts.
    An optional migration message can be included.

``relengapi alebic DBNAME migrate [--message MESSAGE] [--sql] [--head HEAD] [--splice] [--branch-label BRANCH_LABEL] [--version-path VERSION_PATH] [--rev-id REV_ID]``
    Equivalent to revision --autogenerate. The migration script is populated with changes detected
    automatically. The generated script should to be reviewed and edited as not all types of changes
    can be detected. This command does not make any changes to the database.

``relengapi alebic DBNAME upgrade [--sql] [--tag TAG] <revision>``
    Upgrades the database. If revision isn’t given then "head" is assumed.

``relengapi alebic DBNAME downgrade [--sql] [--tag TAG] <revision>``
    Downgrades the database. If revision isn’t given then -1 is assumed.

``relengapi alebic DBNAME stamp [--sql] [--tag TAG] <revision>``
    Sets the revision in the database to the one given as an argument, without performing any migrations.

``relengapi alebic DBNAME current [--verbose]``
    Shows the current revision of the database.

``relengapi alebic DBNAME history [--rev-range REV_RANGE] [--verbose]``
    Shows the list of migrations. If a range isn’t given then the entire history is shown.

``relengapi alebic DBNAME show <revision>``
    Show the revision denoted by the given symbol.

``relengapi alebic DBNAME merge [--message MESSAGE] [--branch-label BRANCH_LABEL] [--rev-id REV_ID] <revisions>``
    Merge two revisions together. Creates a new migration file.

``relengapi alebic DBNAME heads [--verbose] [--resolve-dependencies]``
    Show current available heads in the script directory.

``relengapi alebic DBNAME branches [--verbose]``
    Show current branch points.


.. _Flask-Migrate: http://flask-migrate.readthedocs.org/en/latest/


