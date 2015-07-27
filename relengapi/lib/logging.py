# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import logging
import os
import structlog
import sys

from datetime import datetime

stdout_log = None
logger = structlog.get_logger()


def setupConsoleLogging(quiet):
    global stdout_log
    root = logging.getLogger('')
    if quiet:
        root.setLevel(logging.WARNING)
    else:
        root.setLevel(logging.NOTSET)
    formatter = logging.Formatter('%(asctime)s %(message)s')

    stdout_log = logging.StreamHandler(sys.stdout)
    stdout_log.setLevel(logging.DEBUG)
    stdout_log.setFormatter(formatter)
    root.addHandler(stdout_log)


class UnstructuredRenderer(structlog.processors.KeyValueRenderer):

    def __call__(self, logger, method_name, event_dict):
        event = event_dict.pop('event')
        if event_dict:
            # if there are other keys, use the parent class to render them
            # and append to the event
            rendered = super(UnstructuredRenderer, self).__call__(
                logger, method_name, event_dict)
            return "%s (%s)" % (event, rendered)
        else:
            return event


def mozdef_format(logger, method_name, event_dict):
    # see http://mozdef.readthedocs.org/en/latest/usage.html#sending-logs-to-mozdef

    # move everything to a 'details' sub-key
    details = event_dict
    event_dict = {'details': details}

    # but pull out the summary/event
    event_dict['summary'] = details.pop('event')
    if not details:
        event_dict.pop('details')

    # and set some other fields based on context
    event_dict['timestamp'] = datetime.utcnow().isoformat()
    event_dict['processid'] = os.getpid()
    event_dict['processname'] = 'relengapi'
    event_dict['source'] = logger.name
    event_dict['severity'] = method_name.upper()
    event_dict['tags'] = ['relengapi']
    return event_dict


def reset_context(**kwargs):
    logger.new(**kwargs)


def configure_logging(app):
    if app.config.get('JSON_STRUCTURED_LOGGING'):
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            mozdef_format,
            structlog.processors.JSONRenderer()
        ]
    else:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            UnstructuredRenderer()
        ]

    if app.config.get('JSON_STRUCTURED_LOGGING') and stdout_log:
        # structlog has combined all of the interesting data into the
        # (JSON-formatted) message, so only log that
        stdout_log.setFormatter(logging.Formatter('%(message)s'))

    structlog.configure(
        context_class=structlog.threadlocal.wrap_dict(dict),
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
