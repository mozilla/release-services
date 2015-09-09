# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import logging

import mock
import mozdef_client
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
@test_context.specialize(config={'MOZDEF_TARGET': 'https://localhost/mozdef'})
def test_mozdef(app):
    sent = []
    orig_MozDefEvent = mozdef_client.MozDefEvent
    with mock.patch('mozdef_client.MozDefEvent') as MozDefEvent:
        def constructor(target):
            msg = orig_MozDefEvent(target)
            msg.send = lambda: sent.append(msg)
            return msg
        MozDefEvent.side_effect = constructor

        logger = structlog.get_logger(__name__)
        logger.warn("unseen")
        logger.warn("test message", mozdef=True)
        logger.warn("with attr", attr="foo", mozdef=True)

    # check that 'unseen' wasn't seen, since mozdef was not true
    eq_({m.summary for m in sent}, {"test message", "with attr"})

    # check a few other fields in one of the messages
    msg = sent[0]
    eq_(msg.source, __name__)
    eq_(msg._severity, orig_MozDefEvent.SEVERITY_WARNING)
    eq_(msg.tags, ['relengapi'])

    # and verify that the attribute showed up in details
    assert any([m.details.get('attr') == 'foo' for m in sent])
