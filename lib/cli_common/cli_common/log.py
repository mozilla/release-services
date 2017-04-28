# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import structlog
import logbook
import structlog.exceptions


class UnstructuredRenderer(structlog.processors.KeyValueRenderer):

    def __call__(self, logger, method_name, event_dict):
        event = None
        if 'event' in event_dict:
            event = event_dict.pop('event')
        if event_dict or event is None:
            # if there are other keys, use the parent class to render them
            # and append to the event
            rendered = super(UnstructuredRenderer, self).__call__(
                logger, method_name, event_dict)
            return "%s (%s)" % (event, rendered)
        else:
            return event


def mozdef_sender(target):
    import mozdef_client

    sev_map = {
        'critical': mozdef_client.MozDefEvent.SEVERITY_CRITICAL,
        'error': mozdef_client.MozDefEvent.SEVERITY_ERROR,
        'warning': mozdef_client.MozDefEvent.SEVERITY_WARNING,
        'info': mozdef_client.MozDefEvent.SEVERITY_INFO,
        'debug': mozdef_client.MozDefEvent.SEVERITY_DEBUG,
    }

    def send(logger, method_name, event_dict):
        # only send to mozdef if `mozdef` is set
        if event_dict.pop('mozdef', False):
            msg = mozdef_client.MozDefEvent(target)
            msg.summary = event_dict.get('event', '')
            msg.tags = ['relengapi']
            if set(event_dict) - {'event'}:
                msg.details = event_dict.copy()
                msg.details.pop('event', None)
            msg.source = logger.name
            msg.set_severity(sev_map.get(method_name,
                                         mozdef_client.MozDefEvent.SEVERITY_INFO))
            msg.send()
        # return the message unchanged
        return event_dict
    return send


def init_app(app):
    """
    Init logger from a Flask Application
    """
    mozdef = app.config.get('MOZDEF_TARGET', None)
    level = logbook.ERROR
    if app.debug:
        level = logbook.DEBUG
    init_logger(level=level, mozdef=mozdef)


def init_logger(level=logbook.ERROR, handler=None, mozdef=None):

    # Output logs on stderr
    if handler is None:
        fmt = '{record.channel}: {record.message}'
        handler = logbook.StderrHandler(level=level, format_string=fmt)
    handler.push_application()

    def logbook_factory(*args, **kwargs):
        # Logger given to structlog
        logbook.compat.redirect_logging()
        return logbook.Logger(level=level, *args, **kwargs)

    # Setup structlog over logbook
    processors = [
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # send to mozdef before formatting into a string
    if mozdef:
        processors.append(mozdef_sender(mozdef))

    processors.append(UnstructuredRenderer())

    structlog.configure(
        context_class=structlog.threadlocal.wrap_dict(dict),
        processors=processors,
        logger_factory=logbook_factory,
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(*args, **kwargs):
    return structlog.get_logger(*args, **kwargs)
