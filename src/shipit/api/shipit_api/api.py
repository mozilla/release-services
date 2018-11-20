# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import functools

from flask import abort
from flask import current_app
from flask import g
from flask import jsonify
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import BadRequest

from backend_common.auth import auth
from backend_common.auth0 import mozilla_accept_token
from cli_common.log import get_logger
from cli_common.taskcluster import get_service
from shipit_api.config import PROJECT_NAME
from shipit_api.config import PULSE_ROUTE_REBUILD_PRODUCT_DETAILS
from shipit_api.config import SCOPE_PREFIX
from shipit_api.models import Phase
from shipit_api.models import Release
from shipit_api.tasks import ActionsJsonNotFound
from shipit_api.tasks import UnsupportedFlavor
from shipit_api.tasks import fetch_actions_json
from shipit_api.tasks import generate_action_hook

logger = get_logger(__name__)


def notify_via_irc(message):
    owners = current_app.config.get('IRC_NOTIFICATIONS_OWNERS')
    channel = current_app.config.get('IRC_NOTIFICATIONS_CHANNEL')

    if owners and channel:
        owners = ': '.join(owners)
        current_app.notify.irc({
            'channel': channel,
            'message': f'{owners}: {message}',
        })


def validate_user(key, checker):
    def wrapper(view_func):
        @functools.wraps(view_func)
        def decorated(*args, **kwargs):
            has_permissions = False
            try:
                has_permissions = checker(g.userinfo[key])
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
    session = g.db.session
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
            partner_urls=current_app.config.get('PARTNERS_URL'),
            github_token=current_app.config.get('GITHUB_TOKEN'),
        )
        session.add(r)
        session.commit()
        release = r.json
    except UnsupportedFlavor as e:
        raise BadRequest(description=e.description)

    notify_via_irc(f'New release ({r.product} {r.version} build{r.build_number}) was just created.')

    return release, 201


def list_releases(product=None, branch=None, version=None, build_number=None,
                  status=['scheduled']):
    session = g.db.session
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
    session = g.db.session
    try:
        release = session.query(Release).filter(Release.name == name).one()
        return release.json
    except NoResultFound:
        abort(404)


def get_phase(name, phase):
    session = g.db.session
    try:
        phase = session.query(Phase) \
            .filter(Release.id == Phase.release_id) \
            .filter(Release.name == name) \
            .filter(Phase.name == phase).one()
        return phase.json
    except NoResultFound:
        abort(404)


@mozilla_accept_token()
@validate_user(key='https://sso.mozilla.com/claim/groups',
               checker=lambda xs: 'vpn_cloudops_shipit' in xs)
def schedule_phase(name, phase):
    session = g.db.session
    try:
        phase = session.query(Phase) \
            .filter(Release.id == Phase.release_id) \
            .filter(Release.name == name) \
            .filter(Phase.name == phase).one()
    except NoResultFound:
        abort(404)

    if phase.submitted:
        abort(409, 'Already submitted!')

    queue = get_service('queue')
    queue.createTask(phase.task_id, phase.rendered)

    phase.submitted = True
    phase.completed_by = flask.g.userinfo['email']
    completed = datetime.datetime.utcnow()
    phase.completed = completed
    if all([ph.submitted for ph in phase.release.phases]):
        phase.release.status = 'shipped'
        phase.release.completed = completed
    session.commit()

    notify_via_irc(f'Phase {phase.name} was just scheduled '
                   f'for release {phase.release.product} {phase.release.version} '
                   f'build{phase.release.build_number} - '
                   f'(https://tools.taskcluster.net/groups/{phase.task_id})')

    return phase.json


@mozilla_accept_token()
@validate_user(key='https://sso.mozilla.com/claim/groups',
               checker=lambda xs: 'vpn_cloudops_shipit' in xs)
def abandon_release(name):
    session = g.db.session
    try:
        r = session.query(Release).filter(Release.name == name).one()
        # Cancel all submitted task groups first
        for phase in filter(lambda x: x.submitted, r.phases):
            try:
                actions = fetch_actions_json(phase.task_id)
            except ActionsJsonNotFound:
                logger.info('Ignoring not completed action task %s', phase.task_id)
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
            logger.info('Cancel phase %s by hook %s', phase.name, hook)
            hooks = get_service('hooks')
            res = hooks.triggerHook(hook['hook_group_id'], hook['hook_id'], hook['hook_payload'])
            logger.debug('Done: %s', res)

        r.status = 'aborted'
        session.commit()
        release = r.json
    except NoResultFound:
        abort(404)

    notify_via_irc(f'Release {r.product} {r.version} build{r.build_number} was just canceled.')

    return release


@auth.require_scopes([SCOPE_PREFIX + '/sync_releases'])
def sync_releases(releases):
    session = g.db.session
    for release in releases:
        try:
            session.query(Release).filter(Release.name == release['name']).one()
            # nothing todo
        except NoResultFound:
            status = 'shipped'
            if not release['shippedAt']:
                status = 'aborted'
            r = Release(
                product=release['product'],
                version=release['version'],
                branch=release['branch'],
                revision=release['mozillaRevision'],
                build_number=release['buildNumber'],
                release_eta=release.get('release_eta'),
                partial_updates=release.get('partials'),
                status=status,
            )
            r.created = release['submittedAt']
            r.completed = release['shippedAt']
            session.add(r)
            session.commit()
    return jsonify({'ok': 'ok'})


@auth.require_scopes([SCOPE_PREFIX + '/rebuild-product-details'])
def rebuild_product_details(options):
    pulse_user = current_app.config['PULSE_USER']
    exchange = f'exchange/{pulse_user}/{PROJECT_NAME}'

    logger.info(f'Sending pulse message `{options}` to queue `{exchange}` for '
                f'route `{PULSE_ROUTE_REBUILD_PRODUCT_DETAILS}`.')

    try:
        current_app.pulse.publish(exchange, PULSE_ROUTE_REBUILD_PRODUCT_DETAILS, options)
    except Exception as e:
        import traceback
        msg = 'Can\'t send notification to pulse.'
        trace = traceback.format_exc()
        logger.error('{0}\nException:{1}\nTraceback: {2}'.format(msg, e, trace))  # noqa

    return flask.jsonify({'ok': 'ok'})


@auth.require_scopes([SCOPE_PREFIX + '/sync_releases'])
def sync_release_datetimes(releases):
    session = flask.g.db.session
    for release in releases:
        try:
            r = session.query(Release).filter(Release.name == release['name']).one()
            r.created = release['submittedAt']
            r.completed = release['shippedAt']
            session.commit()
        except NoResultFound:
            # nothing todo
            pass
    return flask.jsonify({'ok': 'ok'})


@auth.require_scopes([SCOPE_PREFIX + '/update_release_status'])
def update_release_status(name, body):
    session = flask.g.db.session
    try:
        r = session.query(Release).filter(Release.name == name).one()
    except NoResultFound:
        flask.abort(404)

    status = body['status']
    r.status = status
    if status == 'shipped':
        r.completed = datetime.datetime.utcnow()
    session.commit()
    release = r.json

    notify_via_irc(f'Release {r.product} {r.version} build{r.build_number} status changed to `{status}`.')

    return release
