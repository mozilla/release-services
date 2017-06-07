# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from datetime import datetime, timedelta
from flask import current_app
from typing import Tuple
from werkzeug.exceptions import Conflict, NotFound
from .models import Message, Policy
from .channels import send_notifications
from requests import get


def put_message(uid: str, body: dict) -> Tuple[None, int]:
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
        Policy(**{**p, 'frequency': timedelta(**p['frequency']), 'policy_id': new_message.id})
        for p in body['policies']
    ]

    session.add_all(policies)
    session.commit()

    return None, 200


def delete_message(uid: str) -> Tuple[None, int]:
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

        return None, 200
    else:
        raise NotFound('Message with uid "{}" not found'.format(uid))


def get_tick_tock() -> dict:
    """
    Trigger pending notifications according to their notification policies

    :return: Information about notification triggered by this call in JSON format.
    """
    try:
        session = current_app.db.session

        current_time = datetime.now()
        pending_messages = session.query(Message).all()
        if not pending_messages:
            raise NotFound('No pending policies to trigger.')

        notifications = []
        for message in pending_messages:
            # If the message has reached its deadline, delete it
            if current_time > message.deadline:
                session.delete(message)
                continue

            policies = session.query(Policy).filter(Policy.policy_id == message.id).all()
            for policy in policies:
                # Check our policy time frame is in effect
                if policy.stop_timestamp < current_time or current_time < policy.start_timestamp:
                    continue

                # If we have notified already, only notify according to the frequency
                if policy.last_notified and current_time - policy.last_notified < policy.frequency:
                    continue

                identity_uri = '{endpoint}/identity/{identity_name}/{urgency}'.format(endpoint=current_app.config.get('RELENG_NOTIFICATION_IDENTITY_ENDPOINT'),
                                                                                      identity_name=policy.identity,
                                                                                      urgency=policy.urgency)
                identity_preference, *_ = get(identity_uri).json()['preferences']

                notification_info = send_notifications(message, identity_preference)
                notifications.append(notification_info)

                policy.last_notified = current_time

            session.add_all(policies)
        session.commit()

        return {
            'notifications': notifications,
        }

    except (SystemError, KeyboardInterrupt,):
        raise
