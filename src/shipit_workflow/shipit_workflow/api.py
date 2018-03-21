# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import

import os
import flask
import taskcluster
import functools
from shipit_workflow.models import Release, Phase
from cli_common.log import get_logger
from backend_common.auth0 import mozilla_accept_token
from sqlalchemy.orm.exc import NoResultFound
import datetime

log = get_logger(__name__)


def validate_user(key, checker):
    def wrapper(view_func):
        @functools.wraps(view_func)
        def decorated(*args, **kwargs):
            try:
                if checker(flask.g.userinfo[key]):
                    return view_func(*args, **kwargs)
            except (AttributeError, KeyError):
                response_body = {'error': 'missing_userinfo',
                                 'error_description': 'Userinfo is missing'}
                return response_body, 401, {'WWW-Authenticate': 'Bearer'}

            response_body = {'error': 'invalid_permissions',
                             'error_description': 'Check your permissions'}
            return response_body, 401, {'WWW-Authenticate': 'Bearer'}
        return decorated
    return wrapper


# TODO: add machine account check so we can use these to submit releases
@mozilla_accept_token()
@validate_user(key='https://sso.mozilla.com/claim/groups',
               checker=lambda xs: 'releng' in xs)
def add_release(body):

    session = flask.g.db.session
    r = Release(
        product=body['product'],
        version=body['version'],
        branch=body['branch'],
        revision=body['revision'],
        build_number=body['build_number'],
        release_eta=body['release_eta'],
        status='scheduled',
        partial_updates=body.get('partial_updates')
    )
    r.generate_phases()
    session.add(r)
    session.commit()
    return r.json, 201


def list_releases(full=False):
    session = flask.g.db.session
    releases = session.query(Release)
    if not full:
        releases = releases.filter(Release.status == 'scheduled')
    return [r.json for r in releases.all()]


def get_release(name):
    session = flask.g.db.session
    try:
        release = session.query(Release).filter(Release.name == name).one()
        return release.json
    except NoResultFound:
        flask.abort(404)


def get_phase(name, phase):
    session = flask.g.db.session
    try:
        phase = session.query(Phase) \
            .filter(Release.id == Phase.release_id) \
            .filter(Release.name == name) \
            .filter(Phase.name == phase).one()
        return phase.json
    except NoResultFound:
        flask.abort(404)


@mozilla_accept_token()
@validate_user(key='https://sso.mozilla.com/claim/groups',
               checker=lambda xs: 'releng' in xs)
def schedule_phase(name, phase):
    session = flask.g.db.session
    try:
        phase = session.query(Phase) \
            .filter(Release.id == Phase.release_id) \
            .filter(Release.name == name) \
            .filter(Phase.name == phase).one()
    except NoResultFound:
        flask.abort(404)

    if phase.submitted:
        flask.abort(409, 'Already submitted!')

    queue = taskcluster.Queue({
        'credentials': {
            'clientId': os.environ.get('TASKCLUSTER_CLIENT_ID'),
            'accessToken': os.environ.get('TASKCLUSTER_ACCESS_TOKEN')
        },
        'maxRetries': 12
    })
    queue.createTask(phase.task_id, phase.rendered)
    phase.submitted = True
    phase.completed_by = flask.g.userinfo['email']
    phase.completed = datetime.datetime.utcnow()
    if all([ph.submitted for ph in phase.release.phases]):
        phase.release.status = 'shipped'
    session.commit()
    return phase.json
