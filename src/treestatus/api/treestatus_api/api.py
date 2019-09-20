# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import copy
import datetime
import json

import flask
import flask_login
import pytz
import requests
import sqlalchemy as sa
import werkzeug.exceptions

import backend_common.auth
import backend_common.cache
import cli_common.log
import treestatus_api.config
import treestatus_api.models

UNSET = object()
TREE_SUMMARY_LOG_LIMIT = 5
STATUSPAGE_URL = 'https://api.statuspage.io/v1'
STATUSPAGE_ERROR_ON_CREATE = '''Hi,

For some reason we weren't able to create an incident for tree `{tree}`.

Please make sure that an incident is open for every closed tree.
'''
STATUSPAGE_ERROR_ON_CLOSE = '''Hi,

For some reason we weren't able to close an incident for tree `{tree}`.

Please make sure that an incident is closed for every open (or under approval) tree.
'''

log = cli_common.log.get_logger(__name__)


CombinedTree = collections.namedtuple(
    'CombinedTree',
    [
        'tree',
        'message_of_the_day',
        'tags',
        'status',
        'reason',
        'log_id',
        'model',
    ],
)


def _tree_asdict(tree):
    return {
        field: value
        for field, value in tree._asdict().items()
        if field != 'model'
    }


def _get_combined_tree(tree, tags=None, status=None, reason=None, log_id=None):
    '''Combined view of the Tree.

       This also shows status, reason and tags from last Tree Log.
    '''
    result = copy.deepcopy(treestatus_api.config.DEFAULT_TREE)
    result.update(tree.to_dict())

    if tags is not None:
        result['tags'] = json.loads(tags)

    if status is not None:
        result['status'] = status

    if reason is not None:
        result['reason'] = reason

    if log_id is not None:
        result['log_id'] = log_id

    result['model'] = tree

    return CombinedTree(**result)


def _get(item, field, default=UNSET):
    return item.get(field, default)


def _is_unset(item, field):
    return item.get(field, UNSET) == UNSET


def _now():
    return datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)


def _statuspage_data(
    resolved,
    component_id,
    tree,
    status_from,
    status_to,
):
    data = {
        'status': resolved and 'resolved' or 'investigating',
        'components': {
            component_id: resolved and 'operational' or 'major_outage',
        }
    }
    if not resolved:
        data['name'] = f'Tree {tree.tree} closed'
        data['component_ids'] = [component_id]
        data['metadata'] = {
            'treestatus': {
                'tree': tree.tree,
                'status_from': status_from,
                'status_to': status_to,
            },
        }
        data['body'] = (
            f'Message of the day: {tree.message_of_the_day}\n'
            f'Reason: {tree.reason}\n'
        )
    return dict(incident=data)


def _statuspage_send_email_on_error(subject, content, incident_id=None):
    page_id = flask.current_app.config.get('STATUSPAGE_PAGE_ID')
    address = flask.current_app.config.get('STATUSPAGE_NOTIFY_ON_ERROR')
    if not address or not page_id:
        log.error('STATUSPAGE_NOTIFY_ON_ERROR and/or STATUSPAGE_PAGE_ID not defined in app config.')
        return

    link = {
        'href': f'https://manage.statuspage.io/pages/{page_id}',
        'text': 'Visit statuspage',
    }
    if incident_id:
        link = {
            'href': f'https://manage.statuspage.io/pages/{page_id}/incidents/{incident_id}',
            'text': 'Visit statuspage incident',
        }
    flask.current_app.notify.email({
        'address': address,
        'subject': subject,
        'content': content,
        'link': link,
    })


def _statuspage_create_incident(
    headers,
    component_id,
    tree,
    status_from,
    status_to,
):
    page_id = flask.current_app.config.get('STATUSPAGE_PAGE_ID')
    if not page_id:
        log.error('STATUSPAGE_PAGE_ID not defined in app config.')
        return

    data = _statuspage_data(False,
                            component_id,
                            tree,
                            status_from,
                            status_to,
                            )
    log.debug(f'Create statuspage incident for tree `{tree.tree}` under page `{page_id}`', data=data)
    response = requests.post(
        f'{STATUSPAGE_URL}/pages/{page_id}/incidents',
        headers=headers,
        json=data,
    )
    try:
        response.raise_for_status()
    except Exception as e:
        log.exception(e)
        _statuspage_send_email_on_error(
            subject=f'[treestatus] Error when creating statuspage incident',
            content=STATUSPAGE_ERROR_ON_CREATE.format(tree=tree.tree),
        )


def _statuspage_resolve_incident(
    headers,
    component_id,
    tree,
    status_from,
    status_to,
):
    page_id = flask.current_app.config.get('STATUSPAGE_PAGE_ID')
    response = requests.get(
        f'{STATUSPAGE_URL}/pages/{page_id}/incidents/unresolved',
        headers=headers,
    )
    try:
        response.raise_for_status()
    except Exception as e:
        log.exception(e)
        _statuspage_send_email_on_error(
            subject=f'[treestatus] Error when closing statuspage incident',
            content=STATUSPAGE_ERROR_ON_CLOSE.format(tree=tree.tree),
        )
        return

    # last incident with meta.treestatus.tree == tree.tree
    incident_id = None
    incidents = sorted(response.json(), key=lambda x: x['created_at'])
    for incident in incidents:
        if 'id' in incident and \
                'metadata' in incident and \
                'treestatus' in incident['metadata'] and \
                'tree' in incident['metadata']['treestatus'] and \
                incident['metadata']['treestatus']['tree'] == tree.tree:
            incident_id = incident['id']
            break

    if incident_id is None:
        log.error(f'No incident found when closing tree `{tree.tree}`')
        _statuspage_send_email_on_error(
            subject=f'[treestatus] Error when closing statuspage incident',
            content=STATUSPAGE_ERROR_ON_CLOSE.format(tree=tree.tree),
        )
        return

    response = requests.patch(
        f'{STATUSPAGE_URL}/pages/{page_id}/incidents/{incident_id}',
        headers=headers,
        json=_statuspage_data(True,
                              component_id,
                              tree,
                              status_from,
                              status_to,
                              ),
    )
    try:
        response.raise_for_status()
    except Exception as e:
        log.exception(e)
        _statuspage_send_email_on_error(
            subject=f'[treestatus] Error when closing statuspage incident',
            content=STATUSPAGE_ERROR_ON_CLOSE.format(tree=tree.tree),
            incident_id=incident_id,
        )


def _notify_status_change(trees_changes):
    if flask.current_app.config.get('STATUSPAGE_ENABLE'):
        log.debug('Notify statuspage about trees changes.')

        components = flask.current_app.config.get('STATUSPAGE_COMPONENTS', {})
        token = flask.current_app.config.get('STATUSPAGE_TOKEN')
        if not token:
            log.error('STATUSPAGE_PAGE_ID not defined in app config.')
        else:
            headers = {'Authorization': f'OAuth {token}'}

            for tree_change in trees_changes:
                tree, status_from, status_to, tags = tree_change

                if tree.tree not in components.keys():
                    continue

                log.debug(f'Notify statuspage about: {tree.tree}')
                component_id = components[tree.tree]

                # create an accident
                if status_from in ['open', 'approval required'] and status_to == 'closed':
                    _statuspage_create_incident(headers,
                                                component_id,
                                                tree,
                                                status_from,
                                                status_to,
                                                )

                # close an accident
                elif status_from == 'closed' and status_to in ['open', 'approval required']:
                    _statuspage_resolve_incident(headers,
                                                 component_id,
                                                 tree,
                                                 status_from,
                                                 status_to,
                                                 )

    if flask.current_app.config.get('PULSE_TREESTATUS_ENABLE'):
        routing_key_pattern = 'tree/{0}/status_change'
        exchange = flask.current_app.config.get('PULSE_TREESTATUS_EXCHANGE')

        for tree_change in trees_changes:
            tree, status_from, status_to, tags = tree_change

            payload = {'status_from': status_from,
                       'status_to': status_to,
                       'tree': tree.to_dict(),
                       'tags': tags}
            routing_key = routing_key_pattern.format(tree.tree)

            log.info(
                'Sending pulse to {} for tree: {}'.format(
                    exchange,
                    tree.tree,
                ))

            try:
                flask.current_app.pulse.publish(exchange, routing_key, payload)
            except Exception as e:
                import traceback
                msg = 'Can\'t send notification to pulse.'
                trace = traceback.format_exc()
                log.error('{0}\nException:{1}\nTraceback: {2}'.format(msg, e, trace))  # noqa


def _update_tree_status(session, tree, status=None, reason=None, tags=[],
                        message_of_the_day=None):
    '''Update the given tree's status; note that this does not commit
       the session.  Supply a tree object or name.
    '''
    # DDD: we don't really have to do this
    if status is not None:
        tree.status = status
    # DDD: we don't really have to do this
    if reason is not None:
        tree.reason = reason
    if message_of_the_day is not None:
        tree.message_of_the_day = message_of_the_day

    # log it if the reason or status have changed
    if status or reason:
        if status is None:
            status = 'no change'
        if reason is None:
            reason = 'no change'
        log = treestatus_api.models.Log(tree=tree.tree,
                                        when=_now(),
                                        who=flask_login.current_user.get_id(),
                                        status=status,
                                        reason=reason,
                                        tags=tags,
                                        )
        session.add(log)

    backend_common.cache.cache.delete_memoized(_get_tree, tree.tree)


@backend_common.cache.cache.memoize()
def _get_tree(tree):
    session = flask.current_app.db.session

    q = session.query(treestatus_api.models.Tree)
    q = q.distinct(treestatus_api.models.Tree.tree)
    q = q.add_columns(treestatus_api.models.Log._tags,
                      treestatus_api.models.Log.status,
                      treestatus_api.models.Log.reason,
                      treestatus_api.models.Log.id,
                      )
    q = q.outerjoin(treestatus_api.models.Log,
                    treestatus_api.models.Log.tree == treestatus_api.models.Tree.tree)
    q = q.order_by(treestatus_api.models.Tree.tree.desc(),
                   treestatus_api.models.Log.when.desc())
    q = q.filter(treestatus_api.models.Tree.tree == tree)

    result = q.one_or_none()
    if result:
        return _get_combined_tree(*result)


def _get_trees(trees=None):
    session = flask.current_app.db.session

    q = session.query(treestatus_api.models.Tree)
    q = q.distinct(treestatus_api.models.Tree.tree)
    q = q.add_columns(treestatus_api.models.Log._tags,
                      treestatus_api.models.Log.status,
                      treestatus_api.models.Log.reason,
                      treestatus_api.models.Log.id,
                      )
    q = q.outerjoin(treestatus_api.models.Log,
                    treestatus_api.models.Log.tree == treestatus_api.models.Tree.tree)
    q = q.order_by(treestatus_api.models.Tree.tree.desc(),
                   treestatus_api.models.Log.when.desc())

    if trees:
        q = q.filter(treestatus_api.models.Tree.tree.in_(trees))

    return [_get_combined_tree(*result) for result in q.all()]


def v0_get_tree(tree, format=None):
    result = _get_tree(tree)
    if result is None:
        raise werkzeug.exceptions.BadRequest(f'No tree {tree} found.')
    return _tree_asdict(result)


def get_trees():
    return dict(result={tree.tree: _tree_asdict(tree) for tree in _get_trees()})


def get_trees2():
    return dict(result=[i for i in get_trees()['result'].values()])


def _update_tree_log(id, tags=None, reason=None):
    if tags is None and reason is None:
        return

    session = flask.current_app.db.session

    log = session.query(treestatus_api.models.Log).get(id)

    if log is None:
        raise werkzeug.exceptions.BadRequest(f'No tree log for id {id} found.')

    if tags is not None:
        log._tags = json.dumps(tags)
    if reason is not None:
        log.reason = reason


@backend_common.auth.auth.require_permissions([treestatus_api.config.SCOPE_TREES_UPDATE])
def update_log(id, body):
    session = flask.current_app.db.session

    tags = body.get('tags')
    reason = body.get('reason')

    if tags is None and reason is None:
        return

    # update the log table
    _update_tree_log(id, tags, reason)

    # iterate over all stack
    for ch in session.query(treestatus_api.models.StatusChange).all():
        for tree in ch.trees:
            last_state = json.loads(tree.last_state)

            if last_state['current_log_id'] != id:
                continue

            if reason:
                last_state['current_reason'] = reason
            if tags:
                last_state['current_tags'] = tags

            tree.last_state = json.dumps(last_state)

    session.commit()

    return None, 200


@backend_common.auth.auth.require_permissions([treestatus_api.config.SCOPE_TREES_UPDATE])
def update_trees(body):
    session = flask.current_app.db.session

    # fetch all trees
    trees = _get_trees(body['trees'])

    # check that we fetched all the trees
    if len(trees) != len(body['trees']):
        trees_diff = set(body['trees']) - set([t.tree for t in trees])
        raise werkzeug.exceptions.NotFound(f'Could not fetch the following trees: {trees_diff}')

    # check for other restrains
    if _is_unset(body, 'tags') \
            and _get(body, 'status') == 'closed':
        raise werkzeug.exceptions.BadRequest('tags are required when closing a tree')

    if not _is_unset(body, 'remember') and body['remember'] is True:
        if _is_unset(body, 'status') or _is_unset(body, 'reason') or _is_unset(body, 'tags'):
            raise werkzeug.exceptions.BadRequest(
                'must specify status, reason and tags to remember the change')

    # update the trees as requested
    new_status = _get(body, 'status', None)
    new_reason = _get(body, 'reason', None)
    new_motd = _get(body, 'message_of_the_day', None)
    new_tags = _get(body, 'tags', [])

    old_trees = dict()
    trees_status_change = []

    for tree in trees:
        old_trees[tree.tree] = dict()
        old_trees[tree.tree]['status'] = tree.status
        old_trees[tree.tree]['reason'] = tree.reason
        old_trees[tree.tree]['tags'] = tree.tags
        old_trees[tree.tree]['log_id'] = tree.log_id

        _update_tree_status(session, tree.model,
                            status=new_status,
                            reason=new_reason,
                            message_of_the_day=new_motd,
                            tags=new_tags,
                            )

        if new_status and tree.status != new_status:
            trees_status_change.append((tree, tree.status, new_status, new_tags))

    if not _is_unset(body, 'remember') and body['remember'] is True:

        # add a new stack entry with the new and existing states
        ch = treestatus_api.models.StatusChange(
            who=flask_login.current_user.get_id(),
            reason=body['reason'],
            when=_now(),
            status=body['status'],
        )

        # re-fetch new updated trees
        new_trees = _get_trees(body['trees'])
        for tree in new_trees:
            stt = treestatus_api.models.StatusChangeTree(
                tree=tree.tree,
                last_state=json.dumps(dict(
                    status=old_trees[tree.tree]['status'],
                    reason=old_trees[tree.tree]['reason'],
                    tags=old_trees[tree.tree]['tags'],
                    log_id=old_trees[tree.tree]['log_id'],
                    # XXX: this should probably not be here
                    current_status=tree.status,
                    current_reason=tree.reason,
                    current_tags=tree.tags,
                    current_log_id=tree.log_id,
                ))
            )
            ch.trees.append(stt)

        session.add(ch)

    session.commit()

    _notify_status_change(trees_status_change)

    return None, 204


@backend_common.auth.auth.require_permissions([treestatus_api.config.SCOPE_TREES_CREATE])
def make_tree(tree, body):
    session = flask.current_app.db.session
    if body['tree'] != tree:
        raise werkzeug.exceptions.BadRequest('Tree names must match')
    t = treestatus_api.models.Tree(
        tree=tree,
        status=body['status'],  # DDD: this is not used anywhere
        reason=body['reason'],  # DDD: this is not used anywhere
        message_of_the_day=body['message_of_the_day'],
    )
    try:
        session.add(t)
        session.commit()
    except (sa.exc.IntegrityError, sa.exc.ProgrammingError):
        raise werkzeug.exceptions.BadRequest('tree already exists')
    return None, 204


def _kill_tree(tree):
    session = flask.current_app.db.session
    t = session.query(treestatus_api.models.Tree).get(tree)
    if not t:
        raise werkzeug.exceptions.NotFound('No such tree')
    session.delete(t)
    # delete from logs and change stack, too
    treestatus_api.models.Log.query.filter_by(tree=tree).delete()
    treestatus_api.models.StatusChangeTree.query.filter_by(tree=tree).delete()
    session.commit()
    backend_common.cache.cache.delete_memoized(_get_tree, tree)


@backend_common.auth.auth.require_permissions([treestatus_api.config.SCOPE_TREES_DELETE])
def kill_tree(tree):
    _kill_tree(tree)
    return None, 204


@backend_common.auth.auth.require_permissions([treestatus_api.config.SCOPE_TREES_DELETE])
def kill_trees(body):
    for tree in body['trees']:
        _kill_tree(tree)
    return None, 204


def get_logs(tree, all=0):
    session = flask.current_app.db.session

    # verify the tree exists first
    t = session.query(treestatus_api.models.Tree).get(tree)
    if not t:
        raise werkzeug.exceptions.NotFound('No such tree')

    logs = []
    q = session.query(treestatus_api.models.Log).filter_by(tree=tree)
    q = q.order_by(treestatus_api.models.Log.when.desc())
    if not all:
        q = q.limit(TREE_SUMMARY_LOG_LIMIT)

    logs = [l.to_dict() for l in q]
    return dict(result=logs)


def v0_get_trees(format=None):
    return get_trees()['result']


def get_tree(tree):
    return dict(result=v0_get_tree(tree))


def get_stack():
    return dict(
        result=[
            i.to_dict()
            for i in treestatus_api.models.StatusChange.query.order_by(
                treestatus_api.models.StatusChange.when.desc())
        ]
    )


@backend_common.auth.auth.require_permissions([treestatus_api.config.SCOPE_REVERT_CHANGES])
def update_stack(id, body=dict()):
    session = flask.current_app.db.session

    change = session.query(treestatus_api.models.StatusChange).get(id)
    if not change:
        raise werkzeug.exceptions.NotFound

    for tree in change.trees:
        last_state = json.loads(tree.last_state)
        last_state['current_tags'] = body.get('tags', last_state['current_tags'])
        last_state['current_reason'] = body.get('reason', last_state['current_reason'])
        _update_tree_log(
            last_state['current_log_id'],
            last_state['current_tags'],
            last_state['current_reason'],
        )
        tree.last_state = json.dumps(last_state)

    # DDD: not really needed (i think)
    change.reason = body.get('reason', change.reason)

    session.commit()

    return None, 200


def _revert_change(id, revert=None):
    if revert not in (0, 1, None):
        raise werkzeug.exceptions.BadRequest('Unexpected value for `revert`')

    session = flask.current_app.db.session
    ch = session.query(treestatus_api.models.StatusChange).get(id)
    if not ch:
        raise werkzeug.exceptions.NotFound

    trees_status_change = []

    if revert:
        for chtree in ch.trees:
            tree = _get_tree(chtree.tree)
            if tree is None:
                # if there's no tree to update, don't worry about it
                pass

            last_state = json.loads(chtree.last_state)
            _update_tree_status(session, tree.model,
                                status=last_state['status'],
                                reason=last_state['reason'],
                                tags=last_state.get('tags', []),
                                )

            if last_state['status'] and tree.status != last_state['status']:
                trees_status_change.append(
                    (tree, tree.status, last_state['status'], last_state.get('tags', [])))

    session.delete(ch)
    session.commit()

    _notify_status_change(trees_status_change)

    return None, 204


@backend_common.auth.auth.require_permissions([treestatus_api.config.SCOPE_REVERT_CHANGES])
def revert_change(id, revert=None):
    return _revert_change(id, revert)


@backend_common.auth.auth.require_permissions([treestatus_api.config.SCOPE_REVERT_CHANGES])
def restore_change(id):
    return _revert_change(id, 1)


@backend_common.auth.auth.require_permissions([treestatus_api.config.SCOPE_REVERT_CHANGES])
def discard_change(id):
    return _revert_change(id, 0)
