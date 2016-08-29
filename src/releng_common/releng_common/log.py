# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import logging
import structlog
import sys


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


def init_app(app):
    mozdef = app.config.get('MOZDEF_TARGET', None)

    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # send to mozdef before formatting into a string
    if mozdef:
        processors.append(mozdef)

    processors.append(UnstructuredRenderer())

    structlog.configure(
        context_class=structlog.threadlocal.wrap_dict(dict),
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()
