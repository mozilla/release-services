# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
from backend_common.db import db
from backend_common.notifications import URGENCY_LEVELS
from .config import PROJECT_PATH_NAME
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Interval, String, Text


class Message(db.Model):
    __tablename__ = PROJECT_PATH_NAME + '_messages'

    id = Column(Integer, primary_key=True)
    uid = Column(String(32), unique=True)
    shortMessage = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    deadline = Column(DateTime, nullable=False)


class Policy(db.Model):
    __tablename__ = PROJECT_PATH_NAME + '_policies'

    id = Column(Integer, primary_key=True)
    identity = Column(String, nullable=False)
    urgency = Column(Enum(*URGENCY_LEVELS, name='notification-urgency-levels'), nullable=False)
    start_timestamp = Column(DateTime, nullable=False)
    stop_timestamp = Column(DateTime, nullable=False)
    last_notified = Column(DateTime, nullable=True)  # This will be null when no notification has been sent yet
    frequency = Column(Interval, nullable=False)
    policy_id = Column(Integer, ForeignKey(Message.id, ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
