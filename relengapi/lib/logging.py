# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import logging
import structlog
import sys

from flask import g

stdout_log = None


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


def add_relengapi(logger, method_name, event_dict):
    event_dict['relengapi'] = True
    return event_dict


def add_request_id(logger, method_name, event_dict):
    try:
        event_dict['request_id'] = g.request_id
    except (AttributeError, RuntimeError):
        # RuntimeError occurs when working outside request context
        pass
    return event_dict


def configure_logging(app):
    if app.config.get('JSON_STRUCTURED_LOGGING'):
        processors = [
            structlog.stdlib.filter_by_level,
            add_relengapi,
            add_request_id,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]
    else:
        processors = [
            structlog.stdlib.filter_by_level,
            add_request_id,
            structlog.stdlib.PositionalArgumentsFormatter(),
            UnstructuredRenderer()
        ]

    if app.config.get('JSON_STRUCTURED_LOGGING') and stdout_log:
        stdout_log.setFormatter(logging.Formatter('%(message)s'))

    structlog.configure(
        context_class=dict,
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
