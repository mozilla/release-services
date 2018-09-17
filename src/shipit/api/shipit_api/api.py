# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import functools
import os

import flask
import taskcluster
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import BadRequest

from backend_common.auth0 import mozilla_accept_token
from cli_common.log import get_logger
from shipit_api.models import Phase
from shipit_api.models import Release
from shipit_api.tasks import ActionsJsonNotFound
from shipit_api.tasks import UnsupportedFlavor
from shipit_api.tasks import fetch_actions_json
from shipit_api.tasks import generate_action_hook

log = get_logger(__name__)
_tc_params = {
    'credentials': {
        'clientId': os.environ.get('TASKCLUSTER_CLIENT_ID'),
        'accessToken': os.environ.get('TASKCLUSTER_ACCESS_TOKEN')
    },
    'maxRetries': 12,
}


def _queue():
    return taskcluster.Queue(_tc_params)


def _hooks():
    return taskcluster.Hooks(_tc_params)


def validate_user(key, checker):
    def wrapper(view_func):
        @functools.wraps(view_func)
        def decorated(*args, **kwargs):
            has_permissions = False
            try:
                has_permissions = checker(flask.g.userinfo[key])
            except (AttributeError, KeyError):
                response_body = {'error': 'missing_userinfo',
                                 'error_description': 'Userinfo is missing'}
                return response_body, 401, {'WWW-Authenticate': 'Bearer'}

            if has_permissions:
                return view_func(*args, **kwargs)
            else:
                response_body = {'error': 'invalid_permissions',
                                 'error_description': 'Check your permissions'}
                return response_body, 401, {'WWW-Authenticate': 'Bearer'}
        return decorated
    return wrapper


@mozilla_accept_token()
@validate_user(key='https://sso.mozilla.com/claim/groups',
               checker=lambda xs: 'vpn_cloudops_shipit' in xs)
def add_release(body):
    session = flask.g.db.session
    r = Release(
        product=body['product'],
        version=body['version'],
        branch=body['branch'],
        revision=body['revision'],
        build_number=body['build_number'],
        release_eta=body.get('release_eta'),
        status='scheduled',
        partial_updates=body.get('partial_updates')
    )
    try:
        r.generate_phases(
            partner_urls=flask.current_app.config.get('PARTNERS_URL'),
            github_token=flask.current_app.config.get('GITHUB_TOKEN'),
        )
        session.add(r)
        session.commit()
        return r.json, 201
    except UnsupportedFlavor as e:
        raise BadRequest(description=e.description)


def list_releases(product=None, branch=None, version=None, build_number=None,
                  status=['scheduled']):
    session = flask.g.db.session
    releases = session.query(Release)
    if product:
        releases = releases.filter(Release.product == product)
    if branch:
        releases = releases.filter(Release.branch == branch)
    if version:
        releases = releases.filter(Release.version == version)
        if build_number:
            releases = releases.filter(Release.build_number == build_number)
    elif build_number:
        raise BadRequest(description='Filtering by build_number without version'
                         ' is not supported.')
    releases = releases.filter(Release.status.in_(status))
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
               checker=lambda xs: 'vpn_cloudops_shipit' in xs)
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

    _queue().createTask(phase.task_id, phase.rendered)
    phase.submitted = True
    phase.completed_by = flask.g.userinfo['email']
    phase.completed = datetime.datetime.utcnow()
    if all([ph.submitted for ph in phase.release.phases]):
        phase.release.status = 'shipped'
    session.commit()
    return phase.json


@mozilla_accept_token()
@validate_user(key='https://sso.mozilla.com/claim/groups',
               checker=lambda xs: 'vpn_cloudops_shipit' in xs)
def abandon_release(name):
    session = flask.g.db.session
    try:
        release = session.query(Release).filter(Release.name == name).one()
        # Cancel all submitted task groups first
        for phase in filter(lambda x: x.submitted, release.phases):
            try:
                actions = fetch_actions_json(phase.task_id)
            except ActionsJsonNotFound:
                log.info('Ignoring not completed action task %s', phase.task_id)
                continue

            hook = generate_action_hook(
                decision_task_id=phase.task_id,
                action_name='cancel-all',
                actions=actions,
            )
            # some parameters contain a lot of entries, so we hit the payload
            # size limit. We don't use this parameter in any case, safe to
            # remove
            for long_param in ('existing_tasks', 'release_history', 'release_partner_config'):
                del hook['context']['parameters'][long_param]
            log.info('Cancel phase %s by hook %s', phase.name, hook)
            res = _hooks().triggerHook(hook['hook_group_id'], hook['hook_id'], hook['hook_payload'])
            log.debug('Done: %s', res)

        release.status = 'aborted'
        session.commit()
        return release.json
    except NoResultFound:
        flask.abort(404)
