from .models import Message
from .config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, \
    RELENG_NOTIFICATION_SOURCE_EMAIL, RELENG_NOTIFICATION_IDENTITY_ENDPOINT
import boto3
from boto3.exceptions import Boto3Error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email_notifications(message: Message, identity_preference: dict) -> dict:
    email_message = MIMEMultipart()

    email_message['Subject'] = message.shortMessage
    email_thread_id = '<{message_uid}@{domain}>'.format(message_uid=message.uid, domain='mozilla-releng.net')
    email_message.add_header('In-Reply-To', email_thread_id)
    email_message.add_header('References', email_thread_id)

    email_body_content = """\
    {body}

    Visit this URL to acknowledge this message: {ack_url}
    """.format(body=message.message, ack_url=message.create_ack_url(identity_preference))
    email_body = MIMEText(email_body_content, 'text')
    try:
        ses = boto3.client('ses', aws_access_key_id=AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name='us-west-2')

        raw_message = {'Data': email_body.as_string()}

        ses.send_raw_email(RawMessage=raw_message,
                           Source=RELENG_NOTIFICATION_SOURCE_EMAIL,
                           Destinations=identity_preference['target'])
    except Boto3Error:
        pass

    return {
        'channel': 'email',
        'message': message.message,
        'uid': message.uid,
        'target': identity_preference['target'],
    }

CHANNEL_MAPPING = {
    'email': send_email_notifications,
}


def send_notifications(message: Message, identity_preference: dict) -> dict:
    return CHANNEL_MAPPING[identity_preference['channel']](message, identity_preference)
