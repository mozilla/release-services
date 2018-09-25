# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import current_app

from cli_common import log

from .models import Message

logger = log.get_logger(__name__)


def send_irc_notification(message: Message, identity_preference: dict) -> dict:
    current_app.notify.irc({
        'channel' if identity_preference['target'].startswith('#') else 'user': identity_preference['target'],
        'message': message.shortMessage,
    })

    return {
        'channel': 'IRC',
        'message': message.shortMessage,
        'uid': message.uid,
        'target': identity_preference['target'],
    }


def send_email_notification(message: Message, identity_preference: dict) -> dict:
    current_app.notify.email({
        'address': identity_preference['target'],
        'content': message.message,
        'subject': message.shortMessage,
        'replyTo': '{message_uid}@{domain}'.format(message_uid=message.uid, domain='mozilla-releng.net'),  # For threads, may not be necessary
    })

    return {
        'channel': 'EMAIL',
        'message': message.message,
        'uid': message.uid,
        'target': identity_preference['target'],
    }


CHANNEL_MAPPING = {
    'EMAIL': send_email_notification,
    'IRC': send_irc_notification,
}


def send_notifications(message: Message, identity_preference: dict) -> dict:
    response = CHANNEL_MAPPING[identity_preference['channel']](message, identity_preference)
    logger.info('{target} notified about {message} on {channel}'.format(
        target=identity_preference['target'],
        message=message,
        channel=identity_preference['channel']
    ))
    return response
