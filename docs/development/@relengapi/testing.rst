Testing
=======

Running Tests
-------------

To run the Releng API tests, you will need to install ``nose``:

.. code-block:: none

    pip install nose

Then, simply run

.. code-block:: none

    relengapi run-tests

passing any arguments you would ordinarily pass to ``nosetests``, using ``--`` to separate relengapi arguments from nose arguments:

.. code-block:: none

    relengapi run-tests -- --verbosity=2 relengapi.tests

Note that RelengAPI uses monkeypatching and is thus sensitive to import orders.
In some cases running ``nosetests`` directly may work, but this depends on luck to get the imports in the right order.
Don't do it.

Test Scripts
------------

Tests should be in modules named with a ``test_`` prefix, located under the blueprint package.
For example, the Jacuzzi Allocator's allocation tests might be in ``jacuzzi-allocator/relengapi/blueprints/jacuzzi_allocator/test_allocation.py``, at a Python path of ``relengapi.blueprints.jacuzzi_allocator.test_allocation``.
For a blueprint with a lot of test scripts, add a ``test`` sub-package.

Very simple test scripts can simply contain functions matching Nose's test pattern.
More complex test scripts can subclass ``unittest.TestCase`` and use the provided assertion methods.
See the Nose documentation for more information.

Test Context
------------

.. py:module:: relengapi.lib.testing.context

Most tests take place in the context of an app, some databases, some data, and so on.

To support, this, use the :py:class:`relengapi.lib.testing.context.TestContext` class.

.. py:class:: TestContext(databases, app_setup, db_setup, db_teardown, reuse_app, config)

    :param databases: list by name of databases to set up
    :param app_setup: application setup function; see below
    :param db_setup: database setup function; see below
    :param db_teardown: database teardown function; see below
    :param reuse_app: if true, only create a single Flask app and re-use it for all test cases
    :param config: application configuration
    :param user: a user object, substituted into ``current_user`` during each request

    A test context acts as a decorator to perform API-specific setup and tear-down for tests.

    This class must always be called with keyword arguments.

    This class automatically creates the tables in the specified databases, equivalent to ``relengapi createdb``.
    This takes place in SQLite in-memory databases.

    To perform setup on the app, such as adding routes, override or pass ``app_setup``, which will be called with the app as the first argument.

    Adding test data is up to the caller, using the ``db_setup`` and ``db_teardown`` methods.
    Both are each called with the Flask app as the first argument.
    The former should insert test data into the DB.
    The latter is only necessary if ``reuse_app`` is set, and should reset the data back to a known state.

    .. py:method:: specialize()

        :returns: specialized :py:class:`TestContext` instance

        This returns a specialized version of the object context.
        Its arguments are identical to those for the constructor.
        This is most useful in decorators where a single test requires a slightly different context from the others.
        For example::

            @test_context.specialize(config={'SOME_OPTION': True})
            def test_works_with_some_option(client):
                ..


:py:class:`TestContext` instances act as decorators for test methods.
The test method indicates the objects it needs from the context by its parameter names.
The options are:

    * ``app`` -- the Flask App
    * ``client`` -- a Flask test client (equivalent to ``app.test_client()``)

    The client is monkey-patched to have a ``post_json`` method which makes a POST with an appropriate content type and a JSON dump of its second argument.

For example ::

    test_context = TestContext(databases=['docs'], reuse_app=True)

    @test_context
    def test_doc_testdata(client):
        eq_(json.loads(client.get('/docs/testdata')), {'a': 10})

Flushing Database Sessions
--------------------------

An application keeps a cache of session objects, which is only flushed after a request.
Sessions cache objects aggressively, so if you need to verify that a database row has been updated, you'll want a fresh session.
You can reset all sessions with ``app.db.flush_sessions()``.

Testing Subcommands
-------------------

If your blueprint defines a subcommand, the :py:mod:`relengapi.lib.testing.subcommands` module may be useful.

.. py:module:: relengapi.lib.testing.subcommands

.. py:function:: run_main(args, settings)

    This function will run the 'relengapi' command with the given args,
    returning its stdout.  `settings` are the settings available to the new app
    (as pointed to by the RELENGAPI_SETTINGS env var).

    This is best used by mocking out the part of the subcommand that actually *does* something, then providing a full range of command-line arguments and verifying that they result in the right values passed to the mock.
