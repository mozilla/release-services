# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import copy
import datetime
import json
from functools import lru_cache

import slugid
import sqlalchemy as sa
import sqlalchemy.orm

import shipit_api.config
from backend_common.db import db
from cli_common.log import get_logger
from shipit_api.release import bump_version
from shipit_api.release import is_eme_free_enabled
from shipit_api.release import is_partner_enabled
from shipit_api.tasks import extract_our_flavors
from shipit_api.tasks import fetch_actions_json
from shipit_api.tasks import find_action
from shipit_api.tasks import find_decision_task_id
from shipit_api.tasks import generate_action_hook
from shipit_api.tasks import generate_action_task
from shipit_api.tasks import render_action_hook
from shipit_api.tasks import render_action_task

log = get_logger(__name__)


class Signoff(db.Model):
    __tablename__ = 'shipit_api_signoffs'
    id = sa.Column(sa.Integer, primary_key=True)
    uid = sa.Column(sa.String, nullable=False, unique=True)
    name = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.Text)
    permissions = sa.Column(sa.String, nullable=False)
    completed = sa.Column(sa.DateTime)
    completed_by = sa.Column(sa.String)
    signed = sa.Column(sa.Boolean, default=False)
    phase_id = sa.Column(sa.Integer, sa.ForeignKey('shipit_api_phases.id'))
    phase = sqlalchemy.orm.relationship('Phase', back_populates='signoffs')

    def __init__(self, uid, name, description, permissions):
        self.uid = uid
        self.name = name
        self.description = description
        self.permissions = permissions

    @property
    def json(self):
        return dict(
            uid=self.uid,
            name=self.name,
            description=self.description,
            permissions=self.permissions,
            completed=self.completed or '',
            completed_by=self.completed_by or '',
            signed=self.signed,
        )


class Phase(db.Model):
    __tablename__ = 'shipit_api_phases'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    submitted = sa.Column(sa.Boolean, nullable=False, default=False)
    task_id = sa.Column(sa.String, nullable=False)
    task = sa.Column(sa.Text, nullable=False)
    context = sa.Column(sa.Text, nullable=False)
    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    completed = sa.Column(sa.DateTime)
    completed_by = sa.Column(sa.String)
    release_id = sa.Column(sa.Integer, sa.ForeignKey('shipit_api_releases.id'))
    release = sqlalchemy.orm.relationship('Release', back_populates='phases')
    signoffs = sqlalchemy.orm.relationship('Signoff', order_by=Signoff.id, back_populates='phase')

    def __init__(self, name, task_id, task, context, submitted=False):
        self.name = name
        self.task_id = task_id
        self.task = task
        self.submitted = submitted
        self.context = context

    @property
    def task_json(self):
        return json.loads(self.task)

    @property
    def context_json(self):
        return json.loads(self.context)

    def rendered(self, extra_context={}):
        context = self.context_json
        if extra_context:
            context.update(extra_context)
        return render_action_task(self.task_json, context)

    def rendered_hook_payload(self, extra_context={}):
        context = self.context_json
        previous_graph_ids = context['input']['previous_graph_ids']
        # The first ID is always the decision task ID. We need to update the
        # remaining tasks' IDs using their names.
        decision_task_id, remaining = previous_graph_ids[0], previous_graph_ids[1:]
        resolved_previous_graph_ids = [decision_task_id]
        other_phases = {p.name: p.task_id for p in self.release.phases}
        for phase_name in remaining:
            resolved_previous_graph_ids.append(other_phases[phase_name])
        context['input']['previous_graph_ids'] = resolved_previous_graph_ids
        if extra_context:
            context.update(extra_context)
        return render_action_hook(self.task_json['hook_payload'], context)

    @property
    def json(self):
        return {
            'name': self.name,
            'submitted': self.submitted,
            'actionTaskId': self.task_id or '',
            'created': self.created or '',
            'completed': self.completed or '',
        }


class Release(db.Model):
    __tablename__ = 'shipit_api_releases'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(80), nullable=False, unique=True)
    product = sa.Column(sa.String, nullable=False)
    version = sa.Column(sa.String, nullable=False)
    branch = sa.Column(sa.String, nullable=False)
    revision = sa.Column(sa.String, nullable=False)
    build_number = sa.Column(sa.Integer, nullable=False)
    release_eta = sa.Column(sa.DateTime)
    status = sa.Column(sa.String)  # TODO: move to Enum: shipped, abandoned, scheduled
    phases = sqlalchemy.orm.relationship('Phase', order_by=Phase.id, back_populates='release')

    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    completed = sa.Column(sa.DateTime)

    def __init__(self, product, version, branch, revision, build_number,
                 release_eta, partial_updates, status):
        self.name = f'{product.capitalize()}-{version}-build{build_number}'
        self.product = product
        self.version = version
        self.branch = branch
        self.revision = revision
        self.build_number = build_number
        # Swagger doesn't let passing null values for strings, we use "falsy"
        # ones instead
        self.release_eta = release_eta or None
        self.partial_updates = partial_updates
        self.status = status

    @property
    def project(self):
        return self.branch.split('/')[-1]

    @staticmethod
    def phase_signoffs(branch, product, phase):
        return [
            Signoff(
                uid=slugid.nice().decode('utf-8'),
                name=req['name'],
                description=req['description'],
                permissions=req['permissions']
            )
            for req in
            shipit_api.config.SIGNOFFS.get(branch, {}).get(product, {}).get(phase, [])
        ]

    def generate_phases(self, partner_urls=None, github_token=None):
        phases = []
        previous_graph_ids = [self.decision_task_id]
        next_version = bump_version(self.version.replace('esr', ''))
        input_common = {
            'build_number': self.build_number,
            'next_version': next_version,
            # specify version rather than relying on in-tree version,
            # so if a version bump happens between the build and an action task
            # revision, we still use the correct version.
            'version': self.version,
            'release_eta': self.release_eta
        }
        if not is_partner_enabled(self.product, self.version):
            input_common['release_enable_partners'] = False
        if not is_eme_free_enabled(self.product, self.version):
            input_common['release_enable_emefree'] = False

        if self.partial_updates:
            input_common['partial_updates'] = {}
            for partial_version, info in self.partial_updates.items():
                input_common['partial_updates'][partial_version] = {
                    'buildNumber': info['buildNumber'],
                    'locales': info['locales']
                }
        target_action = find_action('release-promotion', self.actions)
        kind = target_action['kind']
        for phase in self.release_promotion_flavors():
            input_ = copy.deepcopy(input_common)
            input_['release_promotion_flavor'] = phase['name']
            input_['previous_graph_ids'] = list(previous_graph_ids)
            if kind == 'task':
                action_task_id, action_task, context = generate_action_task(
                    decision_task_id=self.decision_task_id,
                    action_name='release-promotion',
                    input_=input_,
                    actions=self.actions,
                )
                if phase['in_previous_graph_ids']:
                    previous_graph_ids.append(action_task_id)
                phase_obj = Phase(
                    phase['name'], action_task_id, json.dumps(action_task), json.dumps(context))
            elif kind == 'hook':
                hook = generate_action_hook(
                    task_group_id=self.decision_task_id,
                    action_name='release-promotion',
                    actions=self.actions,
                    input_=input_,
                )
                hook_no_context = {k: v for k, v in hook.items() if k != 'context'}
                phase_obj = Phase(
                    name=phase['name'],
                    task_id='',
                    task=json.dumps(hook_no_context),
                    context=json.dumps(hook['context']),
                )
                # we need to update input_['previous_graph_ids'] later, because
                # the task IDs cannot be set for hooks in advance
                if phase['in_previous_graph_ids']:
                    previous_graph_ids.append(phase['name'])
            else:
                raise ValueError(f'Unsupported kind: {kind}')

            phase_obj.signoffs = self.phase_signoffs(self.branch, self.product, phase['name'])
            phases.append(phase_obj)
        self.phases = phases

    @property
    @lru_cache(maxsize=2048)
    def decision_task_id(self):
        return find_decision_task_id(self.project, self.revision)

    @property
    def actions(self):
        return fetch_actions_json(self.decision_task_id)

    def release_promotion_flavors(self):
        relpro = find_action('release-promotion', self.actions)
        avail_flavors = relpro['schema']['properties']['release_promotion_flavor']['enum']
        our_flavors = extract_our_flavors(avail_flavors, self.product,
                                          self.version, self.partial_updates)
        return our_flavors

    @property
    def json(self):
        return {
            'name': self.name,
            'product': self.product,
            'branch': self.branch,
            'project': self.project,
            'version': self.version,
            'revision': self.revision,
            'build_number': self.build_number,
            'release_eta': self.release_eta or '',
            'status': self.status,
            'created': self.created or '',
            'completed': self.completed or '',
            'phases': [p.json for p in self.phases],
        }
