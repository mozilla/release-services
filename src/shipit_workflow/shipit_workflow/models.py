# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import copy
import datetime
import json
from functools import lru_cache

import sqlalchemy as sa
import sqlalchemy.orm

from backend_common.db import db
from cli_common.log import get_logger
from shipit_workflow.partners import get_partner_config_by_url
from shipit_workflow.release import bump_version
from shipit_workflow.release import is_partner_enabled
from shipit_workflow.tasks import extract_our_flavors
from shipit_workflow.tasks import fetch_actions_json
from shipit_workflow.tasks import find_action
from shipit_workflow.tasks import find_decision_task_id
from shipit_workflow.tasks import generate_action_task
from shipit_workflow.tasks import render_action_task

log = get_logger(__name__)


class Phase(db.Model):
    __tablename__ = 'shipit_workflow_phases'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    submitted = sa.Column(sa.Boolean, nullable=False, default=False)
    task_id = sa.Column(sa.String, nullable=False)
    task = sa.Column(sa.Text, nullable=False)
    context = sa.Column(sa.Text, nullable=False)
    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    completed = sa.Column(sa.DateTime)
    completed_by = sa.Column(sa.String)
    release_id = sa.Column(sa.Integer, sa.ForeignKey('shipit_workflow_releases.id'))
    release = sqlalchemy.orm.relationship('Release', back_populates='phases')

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

    @property
    def rendered(self):
        return render_action_task(self.task_json, self.context_json, self.task_id)

    @property
    def json(self):
        return {
            'name': self.name,
            'submitted': self.submitted,
            'actionTaskId': self.task_id,
        }


class Release(db.Model):
    __tablename__ = 'shipit_workflow_releases'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(80), nullable=False, unique=True)
    product = sa.Column(sa.String, nullable=False)
    version = sa.Column(sa.String, nullable=False)
    branch = sa.Column(sa.String, nullable=False)
    revision = sa.Column(sa.String, nullable=False)
    build_number = sa.Column(sa.Integer, nullable=False)
    release_eta = sa.Column(sa.DateTime)
    status = sa.Column(sa.String)
    phases = sqlalchemy.orm.relationship('Phase', order_by=Phase.id, back_populates='release')

    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    completed = sa.Column(sa.DateTime)

    def __init__(self, product, version, branch, revision, build_number,
                 release_eta, partial_updates, status):
        self.name = '{product}-{version}-build{build_number}'.format(
            product=product, version=version, build_number=build_number
        )
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

    def generate_phases(self, partner_urls=None, github_token=None):
        blob = []
        phases = []
        previous_graph_ids = [self.decicion_task_id]
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
        if is_partner_enabled(self.product, self.version) and partner_urls and github_token:
            input_common['release_partner_config'] = {}
            for kind, url in partner_urls.items():
                input_common['release_partner_config'][kind] = get_partner_config_by_url(
                    url, kind, github_token
                )

        if self.partial_updates:
            input_common['partial_updates'] = {}
            for partial_version, info in self.partial_updates.items():
                input_common['partial_updates'][partial_version] = {
                    'buildNumber': info['buildNumber'],
                    'locales': info['locales']
                }
        for phase in self.release_promotion_flavors():
            action_task_input = copy.deepcopy(input_common)
            action_task_input['previous_graph_ids'] = list(previous_graph_ids)
            action_task_input['release_promotion_flavor'] = phase['name']
            action_task_id, action_task, context = generate_action_task(
                action_name='release-promotion',
                action_task_input=action_task_input,
                actions=self.actions,
            )
            blob.append({
                'task_id': action_task_id,
                'task': action_task,
                'status': 'pending'
            })
            if phase['in_previous_graph_ids']:
                previous_graph_ids.append(action_task_id)
            phases.append(Phase(phase['name'], action_task_id, json.dumps(action_task), json.dumps(context)))
        self.phases = phases

    @property
    @lru_cache(maxsize=2048)
    def decicion_task_id(self):
        return find_decision_task_id(self.project, self.revision)

    @property
    def actions(self):
        return fetch_actions_json(self.decicion_task_id)

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
            'phases': [p.json for p in self.phases],
        }
