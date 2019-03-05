# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import json

import flask
import flask_login
import pytz
import sqlalchemy as sa
import werkzeug.exceptions

import backend_common.auth
import backend_common.cache
import cli_common.log
import treestatus_api.config
import treestatus_api.models

UNSET = object()
TREE_SUMMARY_LOG_LIMIT = 5

log = cli_common.log.get_logger(__name__)


def _get(item, field, default=UNSET):
    return item.get(field, default)


def _is_unset(item, field):
    return item.get(field, UNSET) == UNSET


def _now():
    return datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)


def _notify_status_change(trees_changes, tags=[]):
    if flask.current_app.config.get('PULSE_TREESTATUS_ENABLE'):
        routing_key_pattern = 'tree/{0}/status_change'
        exchange = flask.current_app.config.get('PULSE_TREESTATUS_EXCHANGE')

        for tree_change in trees_changes:
            tree, status_from, status_to = tree_change

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
    if status is not None:
        tree.status = status
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

    backend_common.cache.cache.delete_memoized(v0_get_tree, tree.tree)


@backend_common.cache.cache.memoize()
def v0_get_tree(tree, format=None):
    t = flask.current_app.db.session.query(treestatus_api.models.Tree).get(tree)
    if not t:
        raise werkzeug.exceptions.NotFound('No such tree')
    return t.to_dict()


def get_trees():
    session = flask.current_app.db.session
    return dict(result={
        t.tree: t.to_dict()
        for t in session.query(treestatus_api.models.Tree)
    })


def get_trees2():
    return dict(result=[i for i in get_trees()['result'].values()])


@backend_common.auth.auth.require_permissions([f'{treestatus_api.config.SCOPE_PREFIX}/trees/update'])
def update_trees(body):
    session = flask.current_app.db.session
    trees = [
        session.query(treestatus_api.models.Tree).get(t)
        for t in body['trees']
    ]
    if not all(trees):
        raise werkzeug.exceptions.NotFound('one or more trees not found')

    if _is_unset(body, 'tags') \
            and _get(body, 'status') == 'closed':
        raise werkzeug.exceptions.BadRequest('tags are required when closing a tree')

    if not _is_unset(body, 'remember') and body['remember'] is True:
        if _is_unset(body, 'status') or _is_unset(body, 'reason'):
            raise werkzeug.exceptions.BadRequest(
                'must specify status and reason to remember the change')
        # add a new stack entry with the new and existing states
        ch = treestatus_api.models.StatusChange(who=flask_login.current_user.get_id(),
                                                reason=body['reason'],
                                                when=_now(),
                                                status=body['status'],
                                                )
        for tree in trees:
            stt = treestatus_api.models.StatusChangeTree(tree=tree.tree,
                                                         last_state=json.dumps({
                                                             'status': tree.status,
                                                             'reason': tree.reason
                                                             }),
                                                         )
            ch.trees.append(stt)
        session.add(ch)

    # update the trees as requested
    new_status = _get(body, 'status', None)
    new_reason = _get(body, 'reason', None)
    new_motd = _get(body, 'message_of_the_day', None)
    new_tags = _get(body, 'tags', [])

    trees_status_change = []

    for tree in trees:
        current_status = tree.status
        _update_tree_status(session, tree,
                            status=new_status,
                            reason=new_reason,
                            message_of_the_day=new_motd,
                            tags=new_tags,
                            )
        if new_status and current_status != new_status:
            trees_status_change.append((tree, current_status, new_status))

    session.commit()

    _notify_status_change(trees_status_change, new_tags)

    return None, 204


@backend_common.auth.auth.require_permissions([f'{treestatus_api.config.SCOPE_PREFIX}/trees/create'])
def make_tree(tree, body):
    session = flask.current_app.db.session
    if body['tree'] != tree:
        raise werkzeug.exceptions.BadRequest('Tree names must match')
    t = treestatus_api.models.Tree(tree=tree,
                                   status=body['status'],
                                   reason=body['reason'],
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
    backend_common.cache.cache.delete_memoized(v0_get_tree, tree)


@backend_common.auth.auth.require_permissions([f'{treestatus_api.config.SCOPE_PREFIX}/trees/delete'])
def kill_tree(tree):
    _kill_tree(tree)
    return None, 204


@backend_common.auth.auth.require_permissions([f'{treestatus_api.config.SCOPE_PREFIX}/trees/delete'])
def kill_trees(trees):
    for tree in trees:
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


def v0_get_trees(format):
    return get_trees()


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

            last_state = json.loads(chtree.last_state)
            tree = treestatus_api.models.Tree.query.get(chtree.tree)
            if tree is None:
                # if there's no tree to update, don't worry about it
                pass

            current_status = tree.status
            _update_tree_status(session, tree,
                                status=last_state['status'],
                                reason=last_state['reason'],
                                )

            if last_state['status'] and current_status != last_state['status']:
                trees_status_change.append(
                    (tree, current_status, last_state['status']))

    session.delete(ch)
    session.commit()

    _notify_status_change(trees_status_change)

    return None, 204


@backend_common.auth.auth.require_permissions([f'{treestatus_api.config.SCOPE_PREFIX}/recent_changes/revert'])
def revert_change(id, revert=None):
    return _revert_change(id, revert)


@backend_common.auth.auth.require_permissions([f'{treestatus_api.config.SCOPE_PREFIX}/recent_changes/revert'])
def restore_change(id):
    return _revert_change(id, 1)


@backend_common.auth.auth.require_permissions([f'{treestatus_api.config.SCOPE_PREFIX}/recent_changes/revert'])
def discard_change(id):
    return _revert_change(id, 0)
