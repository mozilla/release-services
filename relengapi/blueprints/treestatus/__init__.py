# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import json
import logging
from contextlib import contextmanager

import flask
import sqlalchemy as sa
from flask import Blueprint
from flask import current_app
from flask import url_for
from flask.ext.login import current_user
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import NotFound
from wsme import Unset

from relengapi.blueprints.treestatus import model
from relengapi.blueprints.treestatus import types
from relengapi.lib import angular
from relengapi.lib import api
from relengapi.lib import http
from relengapi.lib import time as relengapi_time
from relengapi.lib.api import apimethod
from relengapi.lib.permissions import p

bp = Blueprint('treestatus', __name__,
               static_folder='static',
               template_folder='templates')

p.treestatus.sheriff.doc('Modify tree status (open and close trees)')
p.treestatus.admin.doc('Administrate treestatus (add, delete, modify trees)')

log = logging.getLogger(__name__)
TREE_SUMMARY_LOG_LIMIT = 5
public_data = http.response_headers(
    ('cache-control', 'no-cache'),
    ('access-control-allow-origin', '*'))


def update_tree_status(session, tree, status=None, reason=None,
                       tags=[], message_of_the_day=None):
    """Update the given tree's status; note that this does not commit
    the session.  Supply a tree object or name."""
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
        l = model.DbLog(
            tree=tree.tree,
            when=relengapi_time.now(),
            who=str(current_user),
            status=status,
            reason=reason,
            tags=tags)
        session.add(l)

    tree_cache_invalidate(tree.tree)


@contextmanager
def _get_mc():
    cfg = current_app.config.get('TREESTATUS_CACHE')
    if not cfg:
        yield None
    else:
        with current_app.memcached.cache(cfg) as mc:
            yield mc


def tree_cache_get(tree):
    with _get_mc() as mc:
        if not mc:
            return None
        data = mc.get(tree.encode('utf-8'))
        if not data:
            return
        return api.loads(types.JsonTree, data.decode('utf-8'))


def tree_cache_set(tree, data):
    with _get_mc() as mc:
        if not mc:
            return None
        j = api.dumps(types.JsonTree, data)
        mc.set(tree.encode('utf-8'), j.encode('utf-8'))


def tree_cache_invalidate(tree):
    with _get_mc() as mc:
        if not mc:
            return None
        mc.delete(tree.encode('utf-8'))


@bp.route('/')
def index():
    return angular.template('index.html',
                            url_for('.static', filename='treestatus.js'),
                            url_for('.static', filename='treestatus.css'),
                            stack=api.get_data(get_stack),
                            trees=api.get_data(get_trees))


@bp.route('/details/<path:tree>')
def show_tree_details(tree):
    return angular.template('tree.html',
                            url_for('.static', filename='treestatus.js'),
                            url_for('.static', filename='treestatus.css'),
                            tree=api.get_data(get_tree, tree),
                            logs=api.get_data(get_logs, tree))


@bp.route('/trees')
@public_data
@apimethod({unicode: types.JsonTree})
def get_trees():
    """
    Get the status of all trees.
    """
    trees = {}
    for t in current_app.db.session('relengapi').query(model.DbTree):
        trees[t.tree] = t.to_json()
    return trees


@bp.route('/v0/trees')
@bp.route('/v0/trees/')
@public_data
def v0_get_trees():
    """
    Get the status of all trees in a format compatible with the old
    treestatus
    """
    trees = api.get_data(get_trees)
    resp = flask.Response(api.dumps({unicode: types.JsonTree}, trees))
    resp.headers['content-type'] = 'application/json'
    return resp


@bp.route('/trees/<path:tree>')
@public_data
@apimethod(types.JsonTree, unicode)
def get_tree(tree):
    """
    Get the status of a single tree.

    This endpoint is cached heavily and is safe to call frequently to verify
    the status of a tree.
    """
    r = tree_cache_get(tree)
    if r:
        return r
    t = current_app.db.session('relengapi').query(model.DbTree).get(tree)
    if not t:
        raise NotFound("No such tree")
    j = t.to_json()
    tree_cache_set(tree, j)
    return j


@bp.route('/v0/trees/<path:tree>')
@public_data
def v0_get_tree(tree):
    """
    Get the status of a single tree in a format compatible with the old
    treestatus
    """
    tree = api.get_data(get_tree, tree)
    resp = flask.Response(api.dumps(types.JsonTree, tree))
    resp.headers['content-type'] = 'application/json'
    return resp


@bp.route('/trees/<path:tree_name>', methods=['PUT'])
@p.treestatus.admin.require()
@apimethod(None, unicode, body=types.JsonTree)
def make_tree(tree_name, body):
    """Make a new tree."""
    session = current_app.db.session('relengapi')
    if body.tree != tree_name:
        raise BadRequest("Tree names must match")
    t = model.DbTree(
        tree=tree_name,
        status=body.status,
        reason=body.reason,
        message_of_the_day=body.message_of_the_day)
    try:
        session.add(t)
        session.commit()
    except (sa.exc.IntegrityError, sa.exc.ProgrammingError):
        raise BadRequest("tree already exists")
    return None, 204


@bp.route('/trees/<path:tree>', methods=['DELETE'])
@p.treestatus.admin.require()
@apimethod(None, unicode)
def kill_tree(tree):
    """Delete a tree."""
    session = current_app.db.session('relengapi')
    t = session.query(model.DbTree).get(tree)
    if not t:
        raise NotFound("No such tree")
    session.delete(t)
    # delete from logs and change stack, too
    model.DbLog.query.filter_by(tree=tree).delete()
    model.DbStatusChangeTree.query.filter_by(tree=tree).delete()
    session.commit()
    tree_cache_invalidate(tree)
    return None, 204


@bp.route('/trees/<path:tree>/logs')
@public_data
@apimethod([types.JsonTreeLog], unicode, int)
def get_logs(tree, all=0):
    """
    Get a log of changes for the given tree.  This is limited to the most recent
    5 entries by default.  Use `?all=1` to get all log entries.
    """
    # verify the tree exists first
    t = current_app.db.session('relengapi').query(model.DbTree).get(tree)
    if not t:
        raise NotFound("No such tree")

    logs = []
    q = current_app.db.session('relengapi').query(
        model.DbLog).filter_by(tree=tree)
    q = q.order_by(model.DbLog.when.desc())
    if not all:
        q = q.limit(TREE_SUMMARY_LOG_LIMIT)

    logs = [l.to_json() for l in q]
    return logs


@bp.route('/stack', methods=['GET'])
@apimethod([types.JsonStateChange])
def get_stack():
    """
    Get the "undo stack" of changes to trees, most recent first.
    """
    tbl = model.DbStatusChange
    return [ch.to_json() for ch in tbl.query.order_by(tbl.when.desc())]


@bp.route('/stack/<int:id>', methods=['DELETE'])
@p.treestatus.sheriff.require()
@apimethod(None, int, int)
def revert_change(id, revert=None):
    """
    Remove the given change from the undo stack.

    With ``?revert=1`` This applies the settings that were
    present before the change to the affected trees.

    With ``?revert=0`` or omitting the revert keyword, it merely removes
    the change from the stack without changing the settings on the tree.
    """
    if revert not in (0, 1, None):
        raise BadRequest("Unexpected value for 'revert'")

    session = current_app.db.session('relengapi')
    ch = session.query(model.DbStatusChange).get(id)
    if not ch:
        raise NotFound

    if revert:
        for chtree in ch.trees:
            last_state = json.loads(chtree.last_state)
            tree = model.DbTree.query.get(chtree.tree)
            if tree is None:
                # if there's no tree to update, don't worry about it
                pass
            update_tree_status(
                session, tree,
                status=last_state['status'],
                reason=last_state['reason'])

    session.delete(ch)
    session.commit()
    return None, 204


@bp.route('/trees', methods=['PATCH'])
@p.treestatus.sheriff.require()
@apimethod(None, body=types.JsonTreeUpdate)
def update_trees(body):
    """
    Update trees' status.

    If the update indicates that the previous state should be saved, then a new
    change will be added to the stack containing the previous status and
    reason.  In this case, both reason and status must be supplied.

    The `tags` property must not be empty if `status` is `closed`.
    """
    session = current_app.db.session('relengapi')
    trees = [session.query(model.DbTree).get(t) for t in body.trees]
    if not all(trees):
        raise NotFound("one or more trees not found")

    if body.status == 'closed' and not body.tags:
        raise BadRequest("tags are required when closing a tree")

    if body.remember:
        if body.status is Unset or body.reason is Unset:
            raise BadRequest("must specify status and reason to remember the change")
        # add a new stack entry with the new and existing states
        ch = model.DbStatusChange(
            who=str(current_user),
            reason=body.reason,
            when=relengapi_time.now(),
            status=body.status)
        for tree in trees:
            stt = model.DbStatusChangeTree(
                tree=tree.tree,
                last_state=json.dumps(
                    {'status': tree.status, 'reason': tree.reason}))
            ch.trees.append(stt)
        session.add(ch)

    # update the trees as requested
    def unset_to_none(x):
        return x if x is not Unset else None
    new_status = unset_to_none(body.status)
    new_reason = unset_to_none(body.reason)
    new_motd = unset_to_none(body.message_of_the_day)
    new_tags = unset_to_none(body.tags) or []

    for tree in trees:
        update_tree_status(session, tree,
                           status=new_status,
                           reason=new_reason,
                           message_of_the_day=new_motd,
                           tags=new_tags)

    session.commit()
    return None, 204
