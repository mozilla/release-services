# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import json
import os
import random
import string
from datetime import datetime
from typing import List

from requests import put

import mohawk
from flask import current_app

'''
Common constants and utilities for releng_notification_* services
'''


CHANNELS = [
    'EMAIL', 'IRC',
]

URGENCY_LEVELS = [
    'LOW', 'NORMAL', 'HIGH',
]


def get_current_app_credentials() -> dict:
    return {
        'id': current_app.config['TASKCLUSTER_CLIENT_ID'],
        'key': current_app.config['TASKCLUSTER_ACCESS_TOKEN'],
        'algorithm': 'sha256',
    }


def generate_random_uid() -> str:
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))


def verify_policy_structure(policy: dict) -> None:
    if any(key not in policy for key in ['frequency', 'identity', 'start_timestamp', 'stop_timestamp', 'urgency']):
        raise KeyError('Policy missing required key')

    if any(freq_key not in policy['frequency'] for freq_key in ['days', 'hours', 'minutes']):
        raise KeyError('Policy frequency missing required key')


def schedule_nagbot_message(message: str, short_message: str, deadline: datetime, policies: List[dict], uid: str=None) -> str:
    '''
    Instantiates a new message to be sent repeatedly by NagBot

    :param message: Long description of message (ie email body)
    :param short_message: Short description of message (ie email subject, IRC message)
    :param deadline: Message expiry date
    :param policies: Notification policies described in dict format
    :param uid: Optionally specify tracking uid. A random uid will be generated if not given

    :return: Tracking uid for the notification
    '''
    for policy in policies:
        verify_policy_structure(policy)

    if uid is None:
        uid = generate_random_uid()

    request_url = current_app.config['RELENG_NOTIFICATION_POLICY_URL'] + '/message/' + uid

    message_body = json.dumps({
        'deadline': deadline.isoformat(),
        'message': message,
        'shortMessage': short_message,
        'policies': policies,
    })

    hawk = mohawk.Sender(get_current_app_credentials(), request_url, 'put',
                         content=message_body, content_type='application/json')

    headers = {
        'Authorization': hawk.request_header,
        'Content-Type': 'application/json',
    }

    # Support dev ssl ca cert
    ssl_dev_ca = current_app.config.get('SSL_DEV_CA')
    if ssl_dev_ca is not None:
        assert os.path.isdir(ssl_dev_ca), 'SSL_DEV_CA must be a dir with hashed dev ca certs'

    response = put(request_url, headers=headers, data=message_body, verify=ssl_dev_ca)
    response.raise_for_status()

    return uid
