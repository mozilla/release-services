# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import sqlalchemy as sa

from flask import Blueprint
from flask import current_app
from flask import url_for
from flask.ext.login import current_user
from relengapi import apimethod
from relengapi.lib import angular
from relengapi.lib import api
from relengapi.lib import time as relengapi_time
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import NotFound

from relengapi import p
from relengapi.blueprints.treestatus import model
from relengapi.blueprints.treestatus import types

bp = Blueprint('treestatus', __name__,
               static_folder='static',
               template_folder='templates')

p.treestatus.sheriff.doc('Modify tree status (open and close trees)')
p.treestatus.admin.doc('Administrate treestatus (add, delete, modify trees)')

log = logging.getLogger(__name__)
TREE_SUMMARY_LOG_LIMIT = 5


# TODO: replicate cache control headers
# TODO: use elasticache
# TODO: rename columns, tables
# TODO: remove user table, tokens
# TODO: test deleting a tree with logs or history
# TODO: add "refresh", run it periodically
# TODO: allow editing reason without affecting stack

def update_tree_status(session, tree, status=None, reason=None, tags=[]):
    """Update the given tree's status; note that this does not commit
    the session.  Supply a tree object or name."""
    if not hasattr(tree, 'tree'):
        tree = session.query(model.DbTree).get(tree)
        if not tree:
            raise NotFound

    if status is not None:
        tree.status = status
    if reason is not None:
        tree.reason = reason

    # log it
    if status or reason:
        l = model.DbLog(
            tree=tree.tree,
            when=relengapi_time.now(),
            who=str(current_user),
            action=status,  # action, status same thing
            reason=reason,
            tags=tags)
        session.add(l)


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
@apimethod({unicode: types.JsonTree})
def get_trees():
    """
    Get the status of all trees.
    """
    trees = {}
    for t in current_app.db.session('treestatus').query(model.DbTree):
        trees[t.tree] = t.to_json()
    return trees


@bp.route('/trees/<path:tree>')
@apimethod(types.JsonTree, unicode)
def get_tree(tree):
    """
    Get the status of a single tree.
    """
    t = current_app.db.session('treestatus').query(model.DbTree).get(tree)
    if not t:
        raise NotFound("No such tree")
    return t.to_json()


@bp.route('/trees/<path:tree_name>', methods=['PUT'])
@p.treestatus.admin.require()
@apimethod(None, unicode, body=types.JsonTree)
def make_tree(tree_name, body):
    """Make a new tree."""
    session = current_app.db.session('treestatus')
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


# TODO: make a generic set-motd method?  Why check that everything else
# matches?  Or just allow updates with optional fields?
@bp.route('/trees/<path:tree_name>', methods=['PATCH'])
@p.treestatus.sheriff.require()
@apimethod(unicode, unicode, body=types.JsonTree)
def modify_tree(tree_name, body):
    """Modify a tree.  This cannot modify the tree's status, reason, or name."""
    session = current_app.db.session('treestatus')
    t = current_app.db.session('treestatus').query(model.DbTree).get(tree_name)
    if not t:
        raise NotFound("No such tree")
    # ensure everything matches
    if body.tree != tree_name:
        raise BadRequest("Tree names must match")
    if body.status != t.status:
        raise BadRequest("Cannot modify status (use UPDATE instead)")
    if body.reason != t.reason:
        raise BadRequest("Cannot modify reason (use UPDATE instead)")
    t.message_of_the_day = body.message_of_the_day
    session.commit()
    return None, 204


@bp.route('/trees/<path:tree>', methods=['DELETE'])
@p.treestatus.admin.require()
@apimethod(None, unicode)
def kill_tree(tree):
    """Delete a tree."""
    session = current_app.db.session('treestatus')
    t = session.query(model.DbTree).get(tree)
    if not t:
        raise NotFound("No such tree")
    session.delete(t)
    session.commit()
    return None, 204


@bp.route('/trees/<path:tree>/logs')
@apimethod([types.JsonTreeLog], unicode, int)
def get_logs(tree, all=0):
    """
    Get a log of changes for the given tree.  This is limited to the most recent
    5 entries by default.  Use `?all=1` to get all log entries.
    """
    # verify the tree exists first
    t = current_app.db.session('treestatus').query(model.DbTree).get(tree)
    if not t:
        raise NotFound("No such tree")

    logs = []
    q = current_app.db.session('treestatus').query(
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
    tbl = model.DbStatusStack
    return [st.to_json() for st in tbl.query.order_by(tbl.when.desc())]


@bp.route('/stack/<int:id>', methods=['REVERT'])
@p.treestatus.sheriff.require()
@apimethod(None, int)
def revert_change(id):
    """
    Revert the given change from the undo stack.

    This applies the settings that were present before the change to the
    affected trees, and deletes the change from the stack.
    """
    session = current_app.db.session('treestatus')
    ch = session.query(model.DbStatusStack).get(id)
    if not ch:
        raise NotFound

    for t in ch.trees:
        # TODO: test last_state is correct
        last_state = json.loads(t.last_state)
        try:
            update_tree_status(
                session, t.tree,
                status=last_state['status'],
                reason=last_state['reason'])
        except NotFound:
            # if there's no tree to update, don't worry about it
            pass

    session.delete(ch)
    session.commit()
    return None, 204


@bp.route('/stack/<int:id>', methods=['DELETE'])
@p.treestatus.sheriff.require()
@apimethod(None, int)
def delete_change(id):
    """
    Delete the given change from the undo stack, without applying it.
    """
    session = current_app.db.session('treestatus')
    ch = session.query(model.DbStatusStack).get(id)
    if not ch:
        raise NotFound

    session.delete(ch)
    session.commit()

    return None, 204


@bp.route('/trees', methods=['UPDATE'])
@p.treestatus.sheriff.require()
@apimethod(None, body=types.JsonTreeUpdate)
def update_trees(body):
    """
    Update trees' status.

    If the update indicates that the previous state should be saved, then a new
    change will be added to the undo stack containing the previous state.
    Otherwise, all affected trees will be removed from the undo stack, which
    may result in changes being removed from the stack when no trees remain.

    The `tags` must not be empty if `status` is `closed`.
    """
    session = current_app.db.session('treestatus')
    trees = [session.query(model.DbTree).get(t) for t in body.trees]
    if not all(trees):
        raise NotFound("one or more trees not found")

    if body.status == 'closed' and not body.tags:
        raise BadRequest("tags are required when closing a tree")

    if body.remember:
        # add a new stack entry with the existing states
        st = model.DbStatusStack(
            who=str(current_user),
            reason=body.reason,
            when=relengapi_time.now(),
            status=body.status)
        for tree in trees:
            stt = model.DbStatusStackTree(
                tree=tree.tree,
                last_state=json.dumps(
                    {'status': tree.status, 'reason': tree.reason}))
            st.trees.append(stt)
        session.add(st)
    else:
        tree_names = set(t.tree for t in trees)
        # delete any stack records for this tree
        for st in session.query(model.DbStatusStack):
            for t in st.trees[:]:
                if t.tree in tree_names:
                    session.delete(t)
                    st.trees.remove(t)
            if not st.trees:
                session.delete(st)

    # update the trees as requested
    for tree in trees:
        update_tree_status(session, tree,
                           status=body.status,
                           reason=body.reason,
                           tags=body.tags)

    session.commit()
    return None, 204
