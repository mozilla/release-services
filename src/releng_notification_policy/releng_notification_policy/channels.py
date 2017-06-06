from .models import Message
from releng_notification_policy.flask import app


def send_irc_notification(message: Message, identity_preference: dict) -> dict:
    app.notify.irc()

    return {
        'channel': 'IRC',
        'message': message.message,
        'uid': message.uid,
        'target': identity_preference['target'],
    }


def send_email_notifications(message: Message, identity_preference: dict) -> dict:
    app.notify.email({
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
    'EMAIL': send_email_notifications,
    'IRC': send_irc_notification,
}


def send_notifications(message: Message, identity_preference: dict) -> dict:
    return CHANNEL_MAPPING[identity_preference['channel']](message, identity_preference)
