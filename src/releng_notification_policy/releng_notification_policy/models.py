# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
from backend_common.db import db
from backend_common.notifications import URGENCY_LEVELS
from .config import PROJECT_PATH_NAME
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Interval, String, Text
from datetime import timedelta


class Message(db.Model):
    __tablename__ = PROJECT_PATH_NAME + '_messages'

    id = Column(Integer, primary_key=True)
    uid = Column(String(32), unique=True)
    shortMessage = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    deadline = Column(DateTime, nullable=False)

    def __repr__(self):
        return 'Message(uid={uid}, shortMessage={short_message}, deadline={deadline})'.format(
            uid=self.uid,
            short_message=self.shortMessage,
            deadline=self.deadline
        )


class Policy(db.Model):
    __tablename__ = PROJECT_PATH_NAME + '_policies'

    id = Column(Integer, primary_key=True)
    identity = Column(String, nullable=False)
    urgency = Column(Enum(*URGENCY_LEVELS, name='notification-urgency-levels'), nullable=False)
    start_timestamp = Column(DateTime, nullable=False)
    stop_timestamp = Column(DateTime, nullable=False)
    last_notified = Column(DateTime, nullable=True)  # This will be null when no notification has been sent yet
    frequency = Column(Interval, nullable=False)
    message_id = Column(Integer, ForeignKey(Message.id, ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    def __repr__(self):
        return 'Policy(id={policy_id}, message_uid={message_uid}, identity={identity_name}, urgency={urgency})'.format(
            policy_id=self.id,
            message_uid=self.message_id,
            identity_name=self.identity,
            urgency=self.urgency
        )

    def to_dict(self):
        '''Return the object as a dict, with the Interval converted to a dict with days, hours, mins'''
        day, hour, minute = timedelta(days=1), timedelta(hours=1), timedelta(minutes=1)
        remaining = self.frequency

        num_days = remaining // day
        remaining -= num_days * day
        num_hours = remaining // hour
        remaining -= num_hours * hour
        num_minutes = remaining // minute

        return {
            'identity': self.identity,
            'urgency': self.urgency,
            'start_timestamp': self.start_timestamp.isoformat(),
            'stop_timestamp': self.stop_timestamp.isoformat(),
            'frequency': {
                'days': num_days,
                'hours': num_hours,
                'minutes': num_minutes,
            },
        }
