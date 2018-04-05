# -*- coding: utf-8 -*-
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint

from backend_common.db import db
from backend_common.notifications import CHANNELS
from backend_common.notifications import URGENCY_LEVELS

from .config import APP_NAME


class Identity(db.Model):
    __tablename__ = APP_NAME + '_identities'

    id = Column(Integer, primary_key=True)
    name = Column(String(32), unique=True)


class Preference(db.Model):
    __tablename__ = APP_NAME + '_preferences'
    __table_args__ = (UniqueConstraint('identity', 'urgency', name='_one_urgency_per_id'),)

    id = Column(Integer, primary_key=True)
    urgency = Column(Enum(*URGENCY_LEVELS, name='notification-urgency-levels'), nullable=False)
    channel = Column(Enum(*CHANNELS, name='notification-channels'), nullable=False)
    target = Column(String, nullable=False)
    identity = Column(Integer, ForeignKey(Identity.id, ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    def to_dict(self):
        return {
            'urgency': self.urgency,
            'channel': self.channel,
            'target': self.target,
        }
