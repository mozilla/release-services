Testing
=======

Running Tests
-------------

To run the Releng API tests, you will need to install ``nose``::

    pip install nose

Then, simply run ``nosetests``.

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

.. py:module:: relengapi.testing

Most tests take place in the context of an app, some databases, some data, and so on.

To support, this, use the :py:class:`relengapi.testing.TestContext` class.

.. py:class:: TestContext(databases, db_setup, db_teardown, reuse_app)

    :param databases: list by name of databases to set up
    :param db_setup: database setup function; see below
    :param db_teardown: database teardown function; see below
    :param reuse_app: if true, only create a single Flask app and re-use it for all test cases

    This class automatically creates the tables in the specified databases, equivalent to ``relengapi createdb``.
    This takes place in SQLite in-memory databases.

    To perform setup on the app, such as adding routes, override or pass ``app_setup``, which will be called with the app as the first argument.

    Adding test data is up to the caller, using the ``db_setup`` and ``db_teardown`` methods.
    Both are each called with the Flask app as the first argument.
    The former should insert test data into the DB.
    The latter is only necessary if ``reuse_app`` is set, and should reset the data back to a known state.
    Both can also be given by subclassing :py:class:`TestContext`.

    .. py:method:: app_setup(app)

        :param app: Flask app

    .. py:method:: db_setup(app)

        :param app: Flask app

    .. py:method:: db_teardown(app)

        :param app: Flask app

:py:class:`TestContext` instances act as decorators for test methods.
The test method indicates the objects it needs from the context by its parameter names.
The options are:

    * ``app`` -- the Flask App
    * ``client`` -- a Flask test client (equivalent to ``app.test_client()``)

For example ::

    test_context = TestContext(databases=['docs'], reuse_app=True)

    @test_context
    def test_doc_testdata(client):
        eq_(json.loads(client.get('/docs/testdata')), {'a': 10})
