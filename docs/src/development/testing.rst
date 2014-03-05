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
