# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime

from flask import abort
from flask import current_app
from flask import g
from flask import jsonify
from flask_login import current_user
from mozilla_version.gecko import FirefoxVersion
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import BadRequest

from backend_common.auth import auth
from cli_common.log import get_logger
from cli_common.taskcluster import get_service
from shipit_api.config import PROJECT_NAME
from shipit_api.config import PULSE_ROUTE_REBUILD_PRODUCT_DETAILS
from shipit_api.config import SCOPE_PREFIX
from shipit_api.models import Phase
from shipit_api.models import Release
from shipit_api.models import Signoff
from shipit_api.tasks import ActionsJsonNotFound
from shipit_api.tasks import UnsupportedFlavor
from shipit_api.tasks import fetch_actions_json
from shipit_api.tasks import generate_action_hook
from shipit_api.tasks import render_action_hook

logger = get_logger(__name__)


def good_version(release):
    '''Can the version be parsed by mozilla_version

    Some ancient versions cannot be parsed by the mozilla_version module. This
    function helps to skip the versions that are not supported.
    Example versions that cannot be parsed:
    1.1, 1.1b1, 2.0.0.1
    '''
    try:
        FirefoxVersion.parse(release['version'])
        return True
    except ValueError:
        return False


def notify_via_irc(message):
    owners = current_app.config.get('IRC_NOTIFICATIONS_OWNERS')
    channel = current_app.config.get('IRC_NOTIFICATIONS_CHANNEL')

    if owners and channel:
        owners = ': '.join(owners)
        current_app.notify.irc({
            'channel': channel,
            'message': f'{owners}: {message}',
        })


@auth.require_scopes([SCOPE_PREFIX + '/add_release'])
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
    releases = [r.json for r in releases.all()]
    # filter out not parsable releases, like 1.1, 1.1b1, etc
    releases = filter(good_version, releases)
    return sorted(releases, key=lambda r: FirefoxVersion.parse(r['version']))


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


@auth.require_scopes([SCOPE_PREFIX + '/schedule_phase'])
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

    for signoff in phase.signoffs:
        if not signoff.signed:
            abort(400, 'Pending signoffs')

    task_or_hook = phase.task_json
    if 'hook_payload' in task_or_hook:
        hooks = get_service('hooks')
        client_id = hooks.options['credentials']['clientId'].decode('utf-8')
        extra_context = {'clientId': client_id}
        result = hooks.triggerHook(
            task_or_hook['hook_group_id'],
            task_or_hook['hook_id'],
            phase.rendered_hook_payload(extra_context=extra_context),
        )
        phase.task_id = result['status']['taskId']
    else:
        queue = get_service('queue')
        client_id = queue.options['credentials']['clientId'].decode('utf-8')
        extra_context = {'clientId': client_id}
        queue.createTask(phase.task_id, phase.rendered(extra_context=extra_context))

    phase.submitted = True
    # TODO: (rok) this should be email
    phase.completed_by = current_user.get_id()
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


@auth.require_scopes([SCOPE_PREFIX + '/abandon_release'])
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
                task_group_id=phase.task_id,
                action_name='cancel-all',
                actions=actions,
                input_={},
            )
            hooks = get_service('hooks')
            client_id = hooks.options['credentials']['clientId'].decode('utf-8')
            hook['context']['clientId'] = client_id
            hook_payload_rendered = render_action_hook(
                payload=hook['hook_payload'],
                context=hook['context'],
                delete_params=['existing_tasks', 'release_history', 'release_partner_config'],
            )
            logger.info('Cancel phase %s by hook %s with payload: %s',
                        phase.name, hook['hook_id'], hook_payload_rendered)
            res = hooks.triggerHook(
                    hook['hook_group_id'], hook['hook_id'], hook_payload_rendered)
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
        logger.error(f'{msg}\nException:{e}\nTraceback: {trace}')
    return jsonify({'ok': 'ok'})


@auth.require_scopes([SCOPE_PREFIX + '/sync_releases'])
def sync_release_datetimes(releases):
    session = g.db.session
    for release in releases:
        try:
            r = session.query(Release).filter(Release.name == release['name']).one()
            r.created = release['submittedAt']
            r.completed = release['shippedAt']
            session.commit()
        except NoResultFound:
            # nothing todo
            pass
    return jsonify({'ok': 'ok'})


@auth.require_scopes([SCOPE_PREFIX + '/update_release_status'])
def update_release_status(name, body):
    session = g.db.session
    try:
        r = session.query(Release).filter(Release.name == name).one()
    except NoResultFound:
        abort(404)

    status = body['status']
    r.status = status
    if status == 'shipped':
        r.completed = datetime.datetime.utcnow()
    session.commit()
    release = r.json

    notify_via_irc(f'Release {r.product} {r.version} build{r.build_number} status changed to `{status}`.')

    return release


def get_phase_signoff(name, phase):
    session = g.db.session
    try:
        phase = session.query(Phase) \
            .filter(Release.id == Phase.release_id) \
            .filter(Release.name == name) \
            .filter(Phase.name == phase).one()
        signoffs = [s.json for s in phase.signoffs]
        return dict(signoffs=signoffs)
    except NoResultFound:
        abort(404)


@auth.require_scopes([SCOPE_PREFIX + '/phase_signoff'])
def phase_signoff(name, phase, uid):
    session = g.db.session
    try:
        signoff = session.query(Signoff) \
            .filter(Signoff.uid == uid).one()
    except NoResultFound:
        abort(404, 'Sign off does not exist')

    if signoff.signed:
        abort(409, 'Already signed off')

    # TODO: (rok) this should be email
    who = current_user.get_id()
    # TODO: (rok) transform signoff permissions to scopes
    permissions = [i for i in signoff.permissions]
    if not current_user.has_permissions(permissions):
        abort(401, f'Required LDAP group: `{signoff.permissions}`')

    try:
        # Prevent the same user signing off for multiple signoffs
        phase_obj = session.query(Phase) \
            .filter(Release.id == Phase.release_id) \
            .filter(Release.name == name) \
            .filter(Phase.name == phase).one()
    except NoResultFound:
        abort(404, 'Phase not found')

    if who in [s.completed_by for s in phase_obj.signoffs]:
        abort(409, f'Already signed off by {who}')

    signoff.completed = datetime.datetime.utcnow()
    signoff.signed = True
    signoff.completed_by = who

    session.commit()
    signoffs = [s.json for s in phase_obj.signoffs]

    # Schedule the phase when all signoffs are done
    if all([s.signed for s in phase_obj.signoffs]):
        schedule_phase(name, phase)

    r = phase_obj.release
    notify_via_irc(
        f'{phase} of {r.product} {r.version} build{r.build_number} signed off by {who}.')

    return dict(signoffs=signoffs)
