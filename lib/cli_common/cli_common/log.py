# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import structlog
import logbook
import structlog.exceptions


CHANNELS = [
    'master',
    'staging',
    'production',
]


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
            return '%s (%s)' % (event, rendered)
        else:
            return event


def setup_mozdef(project_name, channel, MOZDEF):
    '''
    Setup mozdef using taskcluster secrets
    '''

    import mozdef_client

    sevirity_map = {
        'critical': mozdef_client.MozDefEvent.SEVERITY_CRITICAL,
        'error': mozdef_client.MozDefEvent.SEVERITY_ERROR,
        'warning': mozdef_client.MozDefEvent.SEVERITY_WARNING,
        'info': mozdef_client.MozDefEvent.SEVERITY_INFO,
        'debug': mozdef_client.MozDefEvent.SEVERITY_DEBUG,
    }

    def send(logger, method_name, event_dict):

        # only send to mozdef if `mozdef` is set
        if event_dict.pop('mozdef', False):
            msg = mozdef_client.MozDefEvent(MOZDEF)

            msg.summary = event_dict.get('event', '')
            msg.tags = [
                'mozilla-releng/services/' + channel,
                project_name,
            ]

            if set(event_dict) - {'event'}:
                msg.details = event_dict.copy()
                msg.details.pop('event', None)

            msg.source = logger.name
            msg.set_severity(
                sevirity_map.get(
                    method_name,
                    mozdef_client.MozDefEvent.SEVERITY_INFO,
                ),
            )
            msg.send()

        return event_dict

    return send


def setup_papertrail(project_name, channel, PAPERTRAIL_HOST, PAPERTRAIL_PORT):
    '''
    Setup papertrail account using taskcluster secrets
    '''

    # Setup papertrail
    papertrail = logbook.SyslogHandler(
        application_name='mozilla-releng/services/{}/{}'.format(channel, project_name),
        address=(PAPERTRAIL_HOST, int(PAPERTRAIL_PORT)),
        format_string='{record.time} {record.channel}: {record.message}',
        bubble=True,
    )
    papertrail.push_application()


def setup_sentry(project_name, channel, SENTRY_DSN, flask_app=None):
    '''
    Setup sentry account using taskcluster secrets
    '''

    import raven
    import raven.handlers.logbook

    sentry_client = raven.Client(
        dsn=SENTRY_DSN,
        site=project_name,
        name='mozilla-releng/services',
        environment=channel,
        # TODO:
        # release=read(VERSION) we need to promote that as well via secrets
        # tags=...
        # repos=...
    )

    if flask_app:
        import raven.contrib.flask
        raven.contrib.flask.Sentry(flask_app, client=sentry_client)

    sentry_handler = raven.handlers.logbook.SentryHandler(
        sentry_client,
        level=logbook.WARNING,
        bubble=True,
    )
    sentry_handler.push_application()


def init_logger(project_name,
                channel=None,
                level=logbook.INFO,
                handler=None,
                PAPERTRAIL_HOST=None,
                PAPERTRAIL_PORT=None,
                SENTRY_DSN=None,
                MOZDEF=None,
                flask_app=None,
                ):

    if not channel:
        channel = os.environ.get('APP_CHANNEL')

    if channel and channel not in CHANNELS:
        raise Exception('Initilizing logging with channel `{}`. It should be one of: {}'.format(channel, ', '.join(CHANNELS)))

    # By default output logs on stderr
    if handler is None:
        fmt = '{record.channel}: {record.message}'
        handler = logbook.StderrHandler(level=level, format_string=fmt)

    handler.push_application()

    # Log to papertrail
    if channel and PAPERTRAIL_HOST and PAPERTRAIL_PORT:
        setup_papertrail(project_name, channel, PAPERTRAIL_HOST, PAPERTRAIL_PORT)

    # Log to sentry
    if channel and SENTRY_DSN:
        setup_sentry(project_name, channel, SENTRY_DSN, flask_app)

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
    if channel and MOZDEF:
        processors.append(setup_mozdef(project_name, channel, MOZDEF))

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
