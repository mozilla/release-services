# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sqlalchemy as sa

from relengapi.lib import db
from relengapi.util import tz
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Index

from relengapi.blueprints.slaveloan import rest

_tbl_prefix = 'slaveloan_'


class Machines(db.declarative_base('relengapi'), db.UniqueMixin):
    __tablename__ = _tbl_prefix + 'machines'
    id = sa.Column(sa.Integer, primary_key=True)
    fqdn = sa.Column(sa.String(255), nullable=False, unique=True)
    ipaddress = sa.Column(sa.String(18), unique=True)
    loan = relationship("Loans", backref="machine")

    @classmethod
    def unique_hash(cls, fqdn, *args, **kwargs):
        return fqdn

    @classmethod
    def unique_filter(cls, query, fqdn, *args, **kwargs):
        return query.filter(Machines.fqdn == fqdn)

    def to_json(self):
        return dict(id=self.id, fqdn=self.fqdn, ipaddress=self.ipaddress)

    def to_wsme(self):
        return rest.Machine(**self.to_json())


class Humans(db.declarative_base('relengapi'), db.UniqueMixin):
    __tablename__ = _tbl_prefix + 'humans'
    id = sa.Column(sa.Integer, primary_key=True)
    ldap = sa.Column(sa.String(255), nullable=False, unique=True)
    bugzilla = sa.Column(sa.String(255), nullable=False)
    loans = relationship("Loans", backref="human")

    @classmethod
    def unique_hash(cls, ldap, *args, **kwargs):
        return ldap

    @classmethod
    def unique_filter(cls, query, ldap, *args, **kwargs):
        return query.filter(Humans.ldap == ldap)

    def to_json(self):
        return dict(id=self.id, ldap_email=self.ldap, bugzilla_email=self.bugzilla)

    def to_wsme(self):
        return rest.Human(**self.to_json())


class Loans(db.declarative_base('relengapi')):
    __tablename__ = _tbl_prefix + 'loans'
    id = sa.Column(sa.Integer, primary_key=True)
    status = sa.Column(sa.String(50), nullable=False)
    bug_id = sa.Column(sa.Integer, nullable=True)
    human_id = sa.Column(sa.Integer,
                         sa.ForeignKey(_tbl_prefix + 'humans.id'),
                         nullable=False)
    machine_id = sa.Column(sa.Integer,
                           sa.ForeignKey(_tbl_prefix + 'machines.id'),
                           nullable=True)
    history = relationship("History", backref="for_loan")
    manual_actions = relationship("ManualActions", backref="for_loan")
    # Backrefs
    # # human   (Humans)
    # # machine (Machines)

    def to_json(self, sub_meth="to_json"):
        if self.machine_id:
            return dict(id=self.id, status=self.status, bug_id=self.bug_id,
                        human=getattr(self.human, sub_meth)(),
                        machine=getattr(self.machine, sub_meth)())
        else:
            return dict(id=self.id, status=self.status, bug_id=self.bug_id,
                        human=getattr(self.human, sub_meth)(),
                        machine=None)

    def to_wsme(self):
        return rest.Loan(**self.to_json(sub_meth="to_wsme"))


class History(db.declarative_base('relengapi')):
    __tablename__ = _tbl_prefix + 'history'
    id = sa.Column(sa.Integer, primary_key=True)
    loan_id = sa.Column(sa.Integer,
                        sa.ForeignKey(_tbl_prefix + 'loans.id'),
                        nullable=False)
    timestamp = sa.Column(db.UTCDateTime(timezone=True),
                          default=tz.utcnow,
                          nullable=False)
    msg = sa.Column(sa.Text, nullable=False)
    # Backrefs
    # # for_loan  (Loans)

    def to_json(self):
        return dict(id=self.id, loan_id=self.loan_id,
                    timestamp=self.timestamp,
                    msg=self.msg)

    def to_wsme(self):
        return rest.HistoryEntry(**self.to_json())


class ManualActions(db.declarative_base('relengapi')):
    __tablename__ = _tbl_prefix + 'manualactions'
    id = sa.Column(sa.Integer, primary_key=True)
    loan_id = sa.Column(sa.Integer,
                        sa.ForeignKey(_tbl_prefix + 'loans.id'),
                        nullable=False)
    timestamp_start = sa.Column(db.UTCDateTime(timezone=True),
                                default=tz.utcnow,
                                nullable=False)
    timestamp_complete = sa.Column(db.UTCDateTime(timezone=True),
                                   default=None,
                                   nullable=True)
    complete_by = sa.Column(sa.String(255), nullable=True)
    msg = sa.Column(sa.Text, nullable=False)

    # Backrefs
    # # for_loan  (Loan this applies to)

    __table_args__ = (Index("loan_id_idx", "loan_id"), )

    def to_json(self):
        return dict(id=self.id, loan_id=self.loan_id,
                    timestamp_start=self.timestamp_start,
                    timestamp_complete=self.timestamp_complete,
                    complete_by=self.complete_by,
                    msg=self.msg)

    def to_wsme(self):
        return rest.ManualAction(**self.to_json())
