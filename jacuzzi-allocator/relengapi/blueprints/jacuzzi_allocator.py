# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from sqlalchemy import Column, Integer, String, Table, ForeignKey, Index
from sqlalchemy.orm import relationship
from flask import Blueprint
from flask import g
from flask import jsonify
from flask import abort
from relengapi import db

bp = Blueprint('jacuzzi-allocator', __name__)


#### N.B. This is not in production yet!  This is just an example.

allocations = Table(
    'allocations', db.declarative_base('jacuzzi_allocator').metadata,
    Column('machine_id', Integer, ForeignKey('machines.id')),
    Column('builder_id', Integer, ForeignKey('builders.id')),
    Index('unique_relationship', 'machine_id', 'builder_id', unique=True)
)


class Machine(db.declarative_base('jacuzzi_allocator')):
    __tablename__ = 'machines'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    builders = relationship('Builder', secondary=allocations)


class Builder(db.declarative_base('jacuzzi_allocator')):
    __tablename__ = 'builders'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True)
    machines = relationship('Machine', secondary=allocations)


@bp.route('/v1/allocated/all')
@bp.route('/v1/machines')
def allocated_all():
    machines = g.db.session('jacuzzi_allocator').query(
        Machine, Machine.name).all()
    return jsonify(machines=[m.name for m in machines])


@bp.route('/v1/builders')
def builders():
    builders = g.db.session('jacuzzi_allocator').query(
        Builder, Builder.name).all()
    return jsonify(builders=[b.name for b in builders])


@bp.route('/v1/builders/<builder>')
def builder(builder):
    builder = Builder.query.filter_by(name=builder).first()
    if not builder:
        abort(404)
    return jsonify(machines=[m.name for m in builder.machines])


@bp.route('/v1/machines/<machine>')
def machine(machine):
    machine = Machine.query.filter_by(name=machine).first()
    if not machine:
        abort(404)
    return jsonify(builders=[b.name for b in machine.builders])
