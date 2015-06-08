Writing a Blueprint
===================

All API functionality in RelengAPI is implemented in the form of Flask blueprints.
These blueprints nicely isolate related functionality both in the codebase (``relengapi/blueprints/foobar``) and in the API (``https://api.pub.build.mozilla.org/foobar``).

Starting a New Blueprint
------------------------

Pick a name for your blueprint.
This guide will use "bubbler", so it's easy to spot.

Create a new Python package under ``relengapi/blueprints``, with ``static`` and ``templates`` directories for assets.

.. code-block:: none

    mkdir -p relengapi/blueprints/bubbler/{static,templates}
    touch relengapi/blueprints/bubbler/__init__.py

Within ``__init__.py``, create a new blueprint::


    # This Source Code Form is subject to the terms of the Mozilla Public
    # License, v. 2.0. If a copy of the MPL was not distributed with this
    # file, You can obtain one at http://mozilla.org/MPL/2.0/.

    import logging

    from flask import Blueprint
    from relengapi import apimethod

    logger = logging.getLogger(__name__)
    bp = Blueprint('bubbler', __name__,
                static_folder='static',
                template_folder='templates')

And create an API endpoint::

    @bp.route('/bubble')
    @apimethod([unicode])
    def bubble():
        """Release a volume of gas into a liquid"""
        return u"bloop!"

Create a test script, ``relengapi/blueprints/bubbler/test_bubbler.py``::

    # This Source Code Form is subject to the terms of the Mozilla Public
    # License, v. 2.0. If a copy of the MPL was not distributed with this
    # file, You can obtain one at http://mozilla.org/MPL/2.0/.

    import contextlib
    import datetime
    import mock
    import pytz

    from flask import json
    from nose.tools import eq_
    from relengapi.blueprints.badpenny import cleanup
    from relengapi.blueprints.badpenny import cron
    from relengapi.blueprints.badpenny import execution
    from relengapi.blueprints.badpenny import rest
    from relengapi.blueprints.badpenny import tables
    from relengapi.lib import badpenny
    from relengapi.lib.permissions import p
    from relengapi.lib.testing.context import TestContext

    test_context = TestContext()

    @test_context
    def test_bubble(client):
        """Getting /bubbler/bubble should return 'bloop!'"""
        resp = client.get('/bubbler/bubble')
        eq_(json.loads(resp.data)['result'], u"bloop!")

Finally, attach your blueprint to the rest of relengapi by adding it to the list of blueprints in ``relengapi/app.py``::

    blueprints = [_load_bp(n) for n in [
        ..
        "bubbler",
        ..
    ]]

You can now run the unit tests with

.. code-block:: none

    relengapi run-tests

And you can perform the same validation that Travis will with

.. code-block:: none

    bash validate.sh

Get hacking!

