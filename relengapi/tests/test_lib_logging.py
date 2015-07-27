# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import structlog

from nose.tools import eq_
from nose.tools import with_setup
from relengapi.lib import logging as relengapi_logging
from relengapi.lib.testing.context import TestContext


test_context = TestContext()


def reset_stdout_log():
    relengapi_logging.stdout_log = None


def set_stdout_log():
    stdout_log = logging.NullHandler()
    logging.getLogger('').addHandler(stdout_log)
    relengapi_logging.stdout_log = stdout_log


def remove_stdout_log():
    logging.getLogger("").removeHandler(relengapi_logging.stdout_log)
    relengapi_logging.stdout_log = None


@with_setup(reset_stdout_log, remove_stdout_log)
@test_context
def test_setupConsoleLogging_quiet(app):
    relengapi_logging.setupConsoleLogging(True)
    root = logging.getLogger("")
    stdout_log = relengapi_logging.stdout_log
    assert stdout_log in root.handlers
    eq_(root.level, logging.WARNING)


@with_setup(reset_stdout_log, remove_stdout_log)
@test_context
def test_setupConsoleLogging_loud(app):
    relengapi_logging.setupConsoleLogging(False)
    root = logging.getLogger("")
    stdout_log = relengapi_logging.stdout_log
    assert stdout_log in root.handlers
    eq_(root.level, logging.NOTSET)


@with_setup(set_stdout_log, remove_stdout_log)
@test_context.specialize(config={'JSON_STRUCTURED_LOGGING': True})
def test_configure_logging(app):
    hdlr = logging.handlers.BufferingHandler(100)
    logging.getLogger(__name__).addHandler(hdlr)
    try:
        logger = structlog.get_logger(__name__)
        logger.warn("test message")

        # find that event in the handler..
        for rec in hdlr.buffer:
            try:
                data = json.loads(rec.msg)
            except Exception:
                pass
            if data["summary"] == "test message":
                break
        else:
            assert 0, "login exception not logged"

        # check a few other fields
        eq_(data['source'], __name__)
        eq_(data['severity'], 'WARNING')
        eq_(data['tags'], ['relengapi'])
    finally:
        logging.getLogger(__name__).removeHandler(hdlr)
