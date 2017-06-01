# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from datetime import datetime, timedelta
from flask import current_app, request
from typing import Tuple
from .models import Message, Policy
from .channels import send_notifications


def create_problem(code=400, type='about:blank', title='', detail='', extra={}, headers=None) -> Tuple[dict, int, dict]:
    """Create a Problem JSON response according to https://tools.ietf.org/html/rfc7807"""
    problem_json = {
        'title': title,
        'status': code,
        'type': type,
        'detail': detail,
        'instance': request.base_url,
    }
    return {**problem_json, **extra}, code, headers


def put_message(uid: str, body: dict):
    """
    Add a new message to be delivered into the service.

    :param uid: UID of message to track
    :param body: Description of message
    :return:
    """
    try:
        session = current_app.db.session

        # Make sure the message UID doesn't already exist in the DB
        if session.query(Message).filter(Message.uid == uid).count():
            return create_problem(409,
                                  title='Message with uid {uid} already exists'.format(uid=uid),
                                  detail='The provided uid {uid} already corresponds to an instantiated message. '
                                         'Please use a different uid parameter and try again.'.format(uid=uid))

        new_message = Message(uid=uid, shortMessage=body['shortMessage'],
                              message=body['message'], deadline=body['deadline'])
        session.add(new_message)
        session.flush()

        policies = [
            # Overwrite the frequency object input from the API with a db compatible timedelta object
            Policy(**{**p, 'frequency': timedelta(**p['frequency'])}, policy_id=new_message.id)
            for p in body['policies']
        ]

        session.add_all(policies)
        session.commit()

        return None, 200

    except ValueError:
        return None, 400


def delete_message(uid: str):
    """Delete the message with the specified UID"""
    try:
        session = current_app.db.session
        message = session.query(Message).filter(Message.uid == uid).first()
        if message:
            session.delete(message)
            session.commit()

            return None, 200
        else:
            return create_problem(code=404, title='Not Found', detail='Message with uid "{}" not found'.format(uid))

    except ValueError:
        return None, 400


def get_tick_tock():
    """Trigger pending notifications according to their notification policies"""
    try:
        session = current_app.db.session

        current_time = datetime.now()
        pending_messages = session.query(Message).all()
        if not pending_messages:
            return create_problem(code=404, title='Not Found', detail='No pending policies to trigger.')

        notifications = []
        for message in pending_messages:
            policies = session.query(Policy).filter(Policy.policy_id == message.id).all()
            for policy in policies:
                # Check our policy time frame is in effect
                if policy.stop_timestamp < current_time or current_time < policy.start_timestamp:
                    continue

                # If we have notified already, only notify according to the frequency
                if policy.last_notified and current_time - policy.last_notified < policy.frequency:
                    continue

                notification_info = send_notifications(message, policy)
                notifications.append(notification_info)
                policy.last_notified = current_time

            session.add_all(policies)
        session.commit()

        return {
            'notifications': notifications,
        }

    except (SystemError, KeyboardInterrupt,):
        raise
