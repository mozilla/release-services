# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from datetime import datetime, timedelta
from flask import current_app
from typing import Iterator, List, Tuple
from werkzeug.exceptions import Conflict, NotFound
from .models import Message, Policy
from .channels import send_notifications
from requests import get
from simplejson import JSONDecodeError


def get_policies_in_json_serializable_form(notification_policies: List[Policy]) -> List[dict]:
    return [
        policy.to_dict()
        for policy in notification_policies
    ]


def get_message_by_uid(uid: str) -> dict:
    session = current_app.db.session

    message = session.query(Message).filter(Message.uid == uid).first()
    if message:
        notification_policies = session.query(Policy).filter(Policy.message_id == message.id).all()
        policies_dicts = get_policies_in_json_serializable_form(notification_policies)

        return {
            'shortMessage': message.shortMessage,
            'message': message.message,
            'deadline': message.deadline,
            'policies': policies_dicts,
        }
    else:
        raise NotFound('Message with uid {} not found.'.format(uid))


def put_message(uid: str, body: dict) -> None:
    """
    Add a new message to be delivered into the service.

    :param uid: UID of message to track
    :param body: Description of message
    :return: No content, status code
    """
    session = current_app.db.session

    # Make sure the message UID doesn't already exist in the DB
    if session.query(Message).filter(Message.uid == uid).count():
        raise Conflict('Message with uid {uid} already exists'.format(uid=uid))

    new_message = Message(uid=uid, shortMessage=body['shortMessage'],
                          message=body['message'], deadline=body['deadline'])
    session.add(new_message)
    session.flush()

    policies = [
        # Overwrite the frequency object input from the API with a db compatible timedelta object
        Policy(**{**p, 'frequency': timedelta(**p['frequency']), 'message_id': new_message.id})
        for p in body['policies']
    ]

    session.add_all(policies)
    session.commit()

    return None


def delete_message(uid: str) -> None:
    """
    Delete the message with the specified UID

    :param uid: UID of the message to delete.
    :return: No content, status code
    """
    session = current_app.db.session
    message = session.query(Message).filter(Message.uid == uid).first()
    if message:
        session.delete(message)
        session.commit()

        return None
    else:
        raise NotFound('Message with uid "{}" not found'.format(uid))


def determine_message_action(messages: List[Message]) -> Iterator[Tuple[Message, bool]]:
    current_time = datetime.now()
    for message in messages:
        if current_time > message.deadline:
            yield message, True
        else:
            yield message, False


def get_identity_uri_for_actionable_policies(policies: List[Policy]) -> Iterator[Tuple[Policy, str]]:
    current_time = datetime.now()
    for policy in policies:
        # Check our policy time frame is in effect
        if policy.stop_timestamp < current_time or current_time < policy.start_timestamp:
            continue

        # If we have notified already, only notify according to the frequency
        if policy.last_notified and current_time - policy.last_notified < policy.frequency:
            continue

        identity_preference_url = '{endpoint}/identity/{identity_name}/{urgency}'\
            .format(endpoint=current_app.config.get('RELENG_NOTIFICATION_IDENTITY_ENDPOINT'),
                    identity_name=policy.identity,
                    urgency=policy.urgency)

        yield policy, identity_preference_url


def get_tick_tock() -> dict:
    """
    Trigger pending notifications according to their notification policies

    :return: Information about notification triggered by this call in JSON format.
    """
    session = current_app.db.session

    current_time = datetime.now()
    pending_messages = session.query(Message).all()
    if not pending_messages:
        raise NotFound('No pending policies to trigger.')

    notifications = []
    for message, is_past_deadline in determine_message_action(pending_messages):
        if is_past_deadline:
            session.delete(message)
            continue

        policies = session.query(Policy).filter(Policy.message_id == message.id).all()
        for policy, identity_preference_uri in get_identity_uri_for_actionable_policies(policies):
            try:
                identity_preference = get(identity_preference_uri, verify=False).json()['preferences'].pop()

                notification_info = send_notifications(message, identity_preference)
                notifications.append(notification_info)

                policy.last_notified = current_time
            except JSONDecodeError:
                pass

        session.add_all(policies)
    session.commit()

    return {
        'notifications': notifications,
    }
