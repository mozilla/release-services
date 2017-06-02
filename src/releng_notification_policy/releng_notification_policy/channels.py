from .models import Message, Policy


def send_email_notifications(message: Message, policy: Policy) -> dict:
    pass


CHANNEL_MAPPING = {
    'email': send_email_notifications,
}


def send_notifications(message, policy) -> dict:
    return {
        'channel': 'email',
        'message': message.message,
        'shortMessage': message.shortMessage,
        'uid': message.uid,
        'targets': [
            policy.identity,
        ]
    }
