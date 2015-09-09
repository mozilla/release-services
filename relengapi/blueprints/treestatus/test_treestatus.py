# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import datetime
import pprint
from contextlib import contextmanager

import mock
from flask import json
from nose.tools import eq_

from relengapi.blueprints import treestatus
from relengapi.blueprints.treestatus import model
from relengapi.blueprints.treestatus import types
from relengapi.lib import auth
from relengapi.lib.permissions import p
from relengapi.lib.testing.context import TestContext

tree1_json = {
    'tree': 'tree1',
    'status': 'closed',
    'reason': 'because',
    'message_of_the_day': 'enjoy troy',
}


def db_setup(app):
    session = app.db.session('relengapi')
    tree = model.DbTree(
        tree=tree1_json['tree'],
        status=tree1_json['status'],
        reason=tree1_json['reason'],
        message_of_the_day=tree1_json['message_of_the_day'])
    session.add(tree)

    def when(day):
        return datetime.datetime(2015, 7, day, 17, 44, 00)
    for tree, status, when, reason, tags in [
        ('tree1', 'opened', when(13), 'i wanted to', ['a']),
        ('tree1', 'opened', when(15), 'i really wanted to', []),
        ('tree1', 'closed', when(14), 'because', ['a', 'b']),
        ('tree2', 'approval required', when(11), 'so there', []),
    ]:
        l = model.DbLog(
            tree=tree,
            when=when,
            who='dustin',
            status=status,
            reason=reason,
            tags=tags)
        session.add(l)
        when += datetime.timedelta(days=1)
    session.commit()


def db_setup_stack(app):
    for tn in range(3):
        session = app.db.session('relengapi')
        tree = model.DbTree(
            tree='tree%d' % tn,
            status='closed',
            reason=['bug 123', 'bug 456', 'bug 456'][tn],
            message_of_the_day='tree %d' % tn)
        session.add(tree)

    def ls(status, reason):
        return json.dumps({'status': status, 'reason': reason})

    # first change closed tree0 and tree1
    stack = model.DbStatusChange(
        who='dustin', reason='bug 123', status='closed',
        when=datetime.datetime(2015, 7, 14))
    session.add(stack)
    for tree in 'tree0', 'tree1':
        session.add(model.DbStatusChangeTree(tree=tree, stack=stack,
                                             last_state=ls('open', tree)))

    # second change closed tree1 and tree2
    stack = model.DbStatusChange(
        who='dustin', reason='bug 456', status='closed',
        when=datetime.datetime(2015, 7, 16))
    session.add(stack)
    session.add(model.DbStatusChangeTree(tree='tree1', stack=stack,
                                         last_state=ls('closed', 'bug 123')))
    session.add(model.DbStatusChangeTree(tree='tree2', stack=stack,
                                         last_state=ls('open', 'tree2')))

    session.commit()


def userperms(perms, email='user@domain.com'):
    u = auth.HumanUser(email)
    u._permissions = set(perms)
    return u

admin_and_sheriff = userperms([p.treestatus.admin, p.treestatus.sheriff])
admin = userperms([p.treestatus.admin])
sheriff = userperms([p.treestatus.sheriff])

config = {'TREESTATUS_CACHE': 'mock://ts'}

test_context = TestContext(databases=['relengapi'],
                           db_setup=db_setup,
                           config=config)


@contextmanager
def set_time(now):
    with mock.patch('relengapi.lib.time.now') as fake_now:
        fake_now.return_value = now
        yield


def assert_logged(app, tree, status, reason, when=None,
                  who='human:user@domain.com', tags=[]):
    with app.app_context():
        session = app.db.session('relengapi')
        q = session.query(model.DbLog)
        q = q.filter_by(tree=tree)
        q = q.order_by(model.DbLog.when)
        logs = q[:]
        for l in logs:
            if l.status != status:
                continue
            if l.reason != reason:
                continue
            if when and l.when != when:
                continue
            if l.who != who:
                continue
            if l.tags != tags:
                continue
            return  # success!
        pprint.pprint([l.__dict__ for l in logs])
        raise AssertionError("no matching log")


def assert_nothing_logged(app, tree):
    with app.app_context():
        session = app.db.session('relengapi')
        q = session.query(model.DbLog)
        q = q.filter_by(tree=tree)
        q = q.order_by(model.DbLog.when)
        logs = q[:]
        if len(logs) != 3:
            pprint.pprint([l.__dict__ for l in logs[3:]])
            raise AssertionError("logs present beyond those in test data")


def assert_change_last_state(app, change_id, **exp_last_states):
    with app.app_context():
        change = model.DbStatusChange.query.get(change_id)
        got_last_states = {}
        for chtree in change.trees:
            ls = json.loads(chtree.last_state)
            got_last_states[chtree.tree] = (ls['status'], ls['reason'])
        eq_(got_last_states, exp_last_states)

# tests


@test_context.specialize(config={})
def test_memcache_no_config(app):
    """With no cache configured, the (private) memcached functions do nothing"""
    with app.app_context():
        # always misses
        eq_(treestatus.tree_cache_get(u't'), None)
        # always succeed
        eq_(treestatus.tree_cache_set(u't', types.JsonTree()), None)
        eq_(treestatus.tree_cache_invalidate(u't'), None)


@test_context
def test_memcache_functions(app):
    """The (private) memcached functions correctly get, set, and invalidate
    a cached item using a mock cache"""
    with app.app_context():
        tree = types.JsonTree(tree='t', status='o', reason='r',
                              message_of_the_day='motd')
        eq_(treestatus.tree_cache_get(u't'), None)
        treestatus.tree_cache_set(u't', tree)
        eq_(treestatus.tree_cache_get(u't').status, 'o')
        treestatus.tree_cache_invalidate(u't')
        eq_(treestatus.tree_cache_get(u't'), None)


@test_context
def test_index_view(client):
    """Getting /treestatus/ results in an index page"""
    resp = client.get('/treestatus/')
    assert 'TreeListController' in resp.data


@test_context
def test_tree_view(client):
    """Getting /treestatus/tree1 results in a tree detail page"""
    resp = client.get('/treestatus/details/tree1')
    assert 'TreeDetailController' in resp.data


@test_context
def test_get_trees(client):
    """Getting /treestatus/trees results in a dictionary of trees keyed by
    name, with a no-cache header and ACAO *"""
    resp = client.get('/treestatus/trees')
    eq_(json.loads(resp.data)['result'], {'tree1': tree1_json})
    eq_(resp.headers['Cache-Control'], 'no-cache')
    eq_(resp.headers['Access-Control-Allow-Origin'], '*')


@test_context
def test_v0_get_trees(client):
    """Getting /treestatus/v0/trees/ results in a dictionary of trees keyed
    by name, without the usual `result` wrapper, with content-type
    application/json, and with a no-cache header and ACAO *"""
    resp = client.get('/treestatus/v0/trees/')
    eq_(json.loads(resp.data), {'tree1': tree1_json})
    eq_(resp.headers['Content-Type'], 'application/json')
    eq_(resp.headers['Cache-Control'], 'no-cache')
    eq_(resp.headers['Access-Control-Allow-Origin'], '*')


@test_context
def test_v0_get_trees_no_slash(client):
    """Getting /treestatus/v0/trees is the same as /v0/trees/"""
    resp = client.get('/treestatus/v0/trees/')
    eq_(json.loads(resp.data), {'tree1': tree1_json})
    eq_(resp.headers['Content-Type'], 'application/json')
    eq_(resp.headers['Cache-Control'], 'no-cache')
    eq_(resp.headers['Access-Control-Allow-Origin'], '*')


@test_context
def test_v0_get_tree(client):
    """Getting /treestatus/v0/tree/ results in a single tree, without the
    usual `result` wrapper, with content-type application/json, and with a
    no-cache header and ACAO *"""
    resp = client.get('/treestatus/v0/trees/tree1')
    eq_(json.loads(resp.data), tree1_json)
    eq_(resp.headers['Content-Type'], 'application/json')
    eq_(resp.headers['Cache-Control'], 'no-cache')
    eq_(resp.headers['Access-Control-Allow-Origin'], '*')


@test_context
def test_get_tree(client):
    """Getting /treestatus/trees/tree1 results in the tree data, with a
    no-cache header and ACAO *"""
    resp = client.get('/treestatus/trees/tree1')
    eq_(json.loads(resp.data)['result'], tree1_json)
    eq_(resp.headers['Cache-Control'], 'no-cache')
    eq_(resp.headers['Access-Control-Allow-Origin'], '*')


@test_context
def test_get_tree_cached(app, client):
    """Getting /treestatus/trees/tree1 when that tree is cached
    results in a read from the cache"""
    with app.app_context():
        tree = types.JsonTree(tree='tree1', status='o', reason='r',
                              message_of_the_day='motd')
        treestatus.tree_cache_set(u'tree1', tree)
    resp = client.get('/treestatus/trees/tree1')
    eq_(json.loads(resp.data)['result']['status'], 'o')


@test_context
def test_get_tree_nosuch(client):
    """Getting /treestatus/trees/NOSUCH results in a 404"""
    resp = client.get('/treestatus/trees/NOSUCH')
    eq_(resp.status_code, 404)


@test_context.specialize(user=admin)
def test_make_tree(client):
    """Creating a tree makes a new tree with supplied values"""
    resp = client.put('/treestatus/trees/newtree', data=json.dumps(
        dict(tree='newtree', status='open', reason='green',
             message_of_the_day='look right or say goodnight')),
        headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 204)
    resp = client.get('/treestatus/trees/newtree')
    eq_(json.loads(resp.data)['result'], dict(tree='newtree', status='open', reason='green',
                                              message_of_the_day='look right or say goodnight'))


@test_context.specialize(user=sheriff)
def test_make_tree_forbidden(client):
    """Creating a tree without admin privs fails"""
    resp = client.put('/treestatus/trees/tree9', data=json.dumps(
        dict(tree='tree9', status='open', reason='green',
             message_of_the_day='look right or say goodnight')),
        headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 403)


@test_context.specialize(user=admin)
def test_make_tree_wrong_name(client):
    """Creating a tree with a different name in the path and the body fails"""
    resp = client.put('/treestatus/trees/sometree', data=json.dumps(
        dict(tree='othertree', status='open', reason='green',
             message_of_the_day='look right or say goodnight')),
        headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 400)


@test_context.specialize(user=admin)
def test_make_tree_dup_name(client):
    """Creating a tree with an existing name fails"""
    resp = client.get('/treestatus/trees/tree1')
    eq_(resp.status_code, 200)
    resp = client.put('/treestatus/trees/tree1', data=json.dumps(
        dict(tree='tree1', status='open', reason='green',
             message_of_the_day='look right or say goodnight')),
        headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 400)


@test_context.specialize(user=admin, db_setup=db_setup_stack)
def test_delete_tree(app, client):
    """Deleting a tree deletes the tree and any associated logs
    and changes"""
    with app.app_context():
        session = app.db.session('relengapi')
        l = model.DbLog(
            tree='tree1',
            when=datetime.datetime(2015, 6, 15, 17, 44, 00),
            who='jimmy',
            status='halfopen',
            reason='being difficult',
            tags=[])
        session.add(l)
        session.commit()

    resp = client.get('/treestatus/trees/tree1')
    eq_(resp.status_code, 200)
    resp = client.delete('/treestatus/trees/tree1')
    eq_(resp.status_code, 204)
    resp = client.get('/treestatus/trees/tree1')
    eq_(resp.status_code, 404)

    with app.app_context():
        eq_(model.DbLog.query.filter_by(tree='tree1')[:], [])
        eq_(model.DbStatusChangeTree.query.filter_by(tree='tree1')[:], [])


@test_context.specialize(user=sheriff)
def test_delete_tree_no_perms(client):
    """Deleting a tree without admin perms fails"""
    resp = client.delete('/treestatus/trees/tree1')
    eq_(resp.status_code, 403)


@test_context.specialize(user=admin)
def test_delete_tree_nosuch(client):
    """Deleting a tree that does not exist fails"""
    resp = client.delete('/treestatus/trees/99999')
    eq_(resp.status_code, 404)


@test_context
def test_get_logs(client):
    """Getting /treestatus/trees/tree1/logs results in a sorted list of log
    entries (newest first), with a no-cache header and ACAO *"""
    resp = client.get('/treestatus/trees/tree1/logs')
    eq_(json.loads(resp.data)['result'], [{
        'tree': 'tree1',
        'tags': [],
        'who': 'dustin',
        'when': '2015-07-15T17:44:00+00:00',
        'reason': 'i really wanted to',
        'status': 'opened',
    }, {
        'tree': 'tree1',
        'tags': ['a', 'b'],
        'who': 'dustin',
        'when': '2015-07-14T17:44:00+00:00',
        'reason': 'because',
        'status': 'closed',
    }, {
        'tree': 'tree1',
        'tags': ['a'],
        'who': 'dustin',
        'when': '2015-07-13T17:44:00+00:00',
        'reason': 'i wanted to',
        'status': 'opened',
    }
    ])
    eq_(resp.headers['Cache-Control'], 'no-cache')
    eq_(resp.headers['Access-Control-Allow-Origin'], '*')


@test_context
def test_get_logs_all(client, app):
    """Getting /treestatus/trees/tree1/logs with over 5 logs present
    results in only 5 logs, unless given ?all=1"""
    # add the log entries
    session = app.db.session('relengapi')
    for ln in range(5):
        l = model.DbLog(
            tree='tree1',
            when=datetime.datetime(2015, 6, 15, 17, 44, 00),
            who='jimmy',
            status='halfopen',
            reason='being difficult',
            tags=[])
        session.add(l)
    session.commit()

    resp = client.get('/treestatus/trees/tree1/logs')
    eq_(len(json.loads(resp.data)['result']), 5)

    resp = client.get('/treestatus/trees/tree1/logs?all=1')
    eq_(len(json.loads(resp.data)['result']), 8)


@test_context
def test_get_logs_nosuch(client):
    """Getting /treestatus/trees/NOSUCH/logs results in a 404"""
    resp = client.get('/treestatus/trees/NOSUCH/logs')
    eq_(resp.status_code, 404)


@test_context.specialize(db_setup=db_setup_stack)
def test_get_stack(client):
    """Getting /treestatus/stack gets the list of changes, most recent first"""
    resp = client.get('/treestatus/stack')
    res = json.loads(resp.data)
    # sort the tree lists, since order isn't specified
    res['result'][0]['trees'].sort()
    res['result'][1]['trees'].sort()
    eq_(res['result'], [{
        'id': 2,
        'trees': ['tree1', 'tree2'],
        'when': '2015-07-16T00:00:00+00:00',
        'who': 'dustin',
        'reason': 'bug 456',
        'status': 'closed',
    }, {
        'id': 1,
        'trees': ['tree0', 'tree1'],
        'who': 'dustin',
        'when': '2015-07-14T00:00:00+00:00',
        'reason': 'bug 123',
        'status': 'closed',
    }
    ])


@test_context.specialize(db_setup=db_setup_stack, user=sheriff)
def test_revert_stack(app, client):
    """DELETEing /treestatus/stack/N with ?revert=1 undoes the effects of
    that change and removes it from the stack"""
    resp = client.open('/treestatus/stack/2?revert=1', method='DELETE')
    eq_(resp.status_code, 204)

    resp = client.get('/treestatus/trees')
    updated_status = sorted([(t['tree'], t['status'], t['reason'])
                             for t in json.loads(resp.data)['result'].values()])
    eq_(updated_status, [
        ('tree0', 'closed', 'bug 123'),
        ('tree1', 'closed', 'bug 123'),
        ('tree2', 'open', 'tree2'),
    ])

    resp = client.get('/treestatus/stack')
    res = json.loads(resp.data)
    res['result'][0]['trees'].sort()
    eq_(res['result'], [{
        'id': 1,
        'trees': ['tree0', 'tree1'],
        'who': 'dustin',
        'when': '2015-07-14T00:00:00+00:00',
        'reason': 'bug 123',
        'status': 'closed',
    }
    ])

    # reverts are logged, with no tags
    assert_logged(app, 'tree1', 'closed', 'bug 123')
    assert_logged(app, 'tree2', 'open', 'tree2')


@test_context.specialize(db_setup=db_setup_stack, user=admin)
def test_revert_stack_no_perms(app, client):
    """DELETEing a stack (using ?revert=1) without sheriff privs fails"""
    resp = client.open('/treestatus/stack/2?revert=1', method='DELETE')
    eq_(resp.status_code, 403)


@test_context.specialize(db_setup=db_setup_stack, user=sheriff)
def test_revert_stack_nosuch(client):
    """DELETEing /treestatus/stack/N with ?revert=1 where there's no such
    stack ID returns 404"""
    resp = client.open('/treestatus/stack/99?revert=1', method='DELETE')
    eq_(resp.status_code, 404)


@test_context.specialize(db_setup=db_setup_stack, user=sheriff)
def test_revert_stack_badarg(client):
    """DELETEing /treestatus/stack/N with ?revert=<bad_argument> should fail"""
    for arg in (2, -1):
        resp = client.open('/treestatus/stack/2?revert=%s' % arg,
                           method='DELETE')
        eq_(resp.status_code, 400)


@test_context.specialize(db_setup=db_setup_stack, user=sheriff)
def test_delete_stack_change(client):
    """DELETE'ing /treestatus/stack/N removes the change from the stack but does
    not change the trees."""
    resp = client.get('/treestatus/trees')
    eq_(resp.status_code, 200)
    trees_before = json.loads(resp.data)['result']

    resp = client.open('/treestatus/stack/2', method='DELETE')
    eq_(resp.status_code, 204)

    resp = client.get('/treestatus/trees')
    eq_(resp.status_code, 200)
    trees_after = json.loads(resp.data)['result']
    eq_(trees_before, trees_after)

    resp = client.get('/treestatus/stack')
    res = json.loads(resp.data)
    res['result'][0]['trees'].sort()
    eq_(res['result'], [{
        'id': 1,
        'trees': ['tree0', 'tree1'],
        'who': 'dustin',
        'when': '2015-07-14T00:00:00+00:00',
        'reason': 'bug 123',
        'status': 'closed',
    }
    ])


@test_context.specialize(db_setup=db_setup_stack, user=admin)
def test_delete_stack_no_perms(app, client):
    """DELETE'ing a stack without sheriff privs fails"""
    resp = client.open('/treestatus/stack/2', method='DELETE')
    eq_(resp.status_code, 403)


@test_context.specialize(db_setup=db_setup_stack, user=sheriff)
def test_delete_stack_nosuch(client):
    """DELETE'ing /treestatus/stack/N where there's no such stack ID returns 404"""
    resp = client.open('/treestatus/stack/99', method='DELETE')
    eq_(resp.status_code, 404)


@test_context.specialize(user=sheriff)
def test_patch_tree_status(app, client):
    """PATCHing a tree's status changes its status and logs"""
    resp = client.patch('/treestatus/trees', data=json.dumps(
        dict(trees=['tree1'], status='approval required')),
        headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 204)
    resp = client.get('/treestatus/trees/tree1')
    eq_(json.loads(resp.data)['result'],
        dict(tree='tree1', status='approval required',
             reason='because', message_of_the_day="enjoy troy"))
    assert_logged(app, 'tree1', 'approval required', 'no change')


@test_context.specialize(user=sheriff)
def test_patch_tree_reason(app, client):
    """PATCHing a tree's reason changes its reason and logs"""
    resp = client.patch('/treestatus/trees', data=json.dumps(
        dict(trees=['tree1'], reason='slow mac builds')),
        headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 204)
    resp = client.get('/treestatus/trees/tree1')
    eq_(json.loads(resp.data)['result'],
        dict(tree='tree1', status='closed', reason='slow mac builds',
             message_of_the_day="enjoy troy"))
    assert_logged(app, 'tree1', 'no change', 'slow mac builds')


@test_context.specialize(user=sheriff)
def test_patch_tree_motd(app, client):
    """PATCHing a tree's message_of_the_day updates the message but doesn't log"""
    resp = client.patch('/treestatus/trees', data=json.dumps(
        dict(trees=['tree1'], message_of_the_day="if it don't fit force it")),
        headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 204)
    resp = client.get('/treestatus/trees/tree1')
    eq_(json.loads(resp.data)['result'],
        dict(tree='tree1', status='closed', reason='because',
             message_of_the_day="if it don't fit force it"))
    assert_nothing_logged(app, 'tree1')


@test_context.specialize(user=admin)
def test_patch_tree_no_perms(client):
    """PATCHing a tree without sheriff perms fails"""
    resp = client.patch('/treestatus/trees', data=json.dumps(
        dict(trees=['tree1'], status='closed', reason='because',
             message_of_the_day="if it don't fit force it")),
        headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 403)


@test_context.specialize(user=sheriff)
def test_patch_tree_nosuch(client):
    """PATCHing a tree that does not exist returns a 404 error"""
    resp = client.patch('/treestatus/trees', data=json.dumps(
        dict(trees=['nosuch'], status='open', reason='because',
             message_of_the_day="if it don't fit force it")),
        headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 404)


@test_context.specialize(user=sheriff)
def test_patch_tree_tags_required_to_close(client):
    """PATCHing a tree's with status=closed and no tags fails"""
    resp = client.patch('/treestatus/trees', data=json.dumps(
        dict(trees=['tree1'], status='closed')),
        headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 400)


@test_context.specialize(user=sheriff)
def test_patch_tree_status_required_to_remember(client):
    """PATCHing a tree's with remember=true fails without a status"""
    resp = client.patch('/treestatus/trees', data=json.dumps(
        dict(trees=['tree1'], reason='all klear', remember=True)),
        headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 400)


@test_context.specialize(user=sheriff)
def test_patch_tree_reason_required_to_remember(client):
    """PATCHing a tree's with remember=true fails without a rerason"""
    resp = client.patch('/treestatus/trees', data=json.dumps(
        dict(trees=['tree1'], status='open', remember=True)),
        headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 400)


@test_context.specialize(db_setup=db_setup_stack, user=admin)
def test_patch_trees_no_perms(app, client):
    """PATCHing a tree without sherrif perms fails"""
    resp = client.patch('/treestatus/trees', data=json.dumps(
        dict(trees=['tree1'], status='open', reason='because',
             message_of_the_day="if it don't fit force it")),
        headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 403)


@test_context.specialize(db_setup=db_setup_stack, user=sheriff)
def test_patch_trees_no_remember(app, client):
    """PATCHing a tree without remembering changes updates those trees but
    does not clear out the stack for those trees."""
    update = {'trees': ['tree1', 'tree0'], 'status': 'open',
              'reason': 'fire extinguished',
              'tags': [],
              'remember': False}
    resp = client.patch('/treestatus/trees',
                        data=json.dumps(update),
                        headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 204)

    resp = client.get('/treestatus/trees')
    eq_(resp.status_code, 200)
    updated_status = sorted([(t['tree'], t['status'], t['reason'])
                             for t in json.loads(resp.data)['result'].values()])
    eq_(updated_status, [
        ('tree0', 'open', 'fire extinguished'),
        ('tree1', 'open', 'fire extinguished'),
        ('tree2', 'closed', 'bug 456'),
    ])

    resp = client.get('/treestatus/stack')
    res = json.loads(resp.data)
    for st in res['result']:
        st['trees'].sort()
    eq_(res['result'], [{
        'id': 2,
        'trees': ['tree1', 'tree2'],  # tree0, tree1 still present
        'when': '2015-07-16T00:00:00+00:00',
        'who': 'dustin',
        'reason': 'bug 456',
        'status': 'closed',
    }, {
        'id': 1,
        'trees': ['tree0', 'tree1'],
        'who': 'dustin',
        'when': '2015-07-14T00:00:00+00:00',
        'reason': 'bug 123',
        'status': 'closed',
    }
    ])

    assert_logged(app, 'tree0', 'open', 'fire extinguished')
    assert_logged(app, 'tree1', 'open', 'fire extinguished')


@test_context.specialize(db_setup=db_setup_stack, user=sheriff)
def test_patch_trees_closed_without_tags(client):
    """PATCHing trees to close them without tags is a bad request"""
    update = {'trees': ['tree1', 'tree0'], 'status': 'closed',
              'reason': 'bomb damage',
              'tags': [], 'remember': True}
    resp = client.patch('/treestatus/trees',
                        data=json.dumps(update),
                        headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 400)


@test_context.specialize(db_setup=db_setup_stack, user=sheriff)
def test_patch_trees_remember(app, client):
    """PATCHing a tree and remembering changes updates those trees and
    adds a stack entry."""
    update = {'trees': ['tree1', 'tree0'], 'status': 'closed',
              'reason': 'bomb damage',
              'tags': ['c4'], 'remember': True}
    with set_time(datetime.datetime(2015, 7, 21, 0, 0, 0)):
        resp = client.patch('/treestatus/trees',
                            data=json.dumps(update),
                            headers=[('Content-Type', 'application/json')])
    eq_(resp.status_code, 204)

    resp = client.get('/treestatus/trees')
    eq_(resp.status_code, 200)
    updated_status = sorted([(t['tree'], t['status'], t['reason'])
                             for t in json.loads(resp.data)['result'].values()])
    eq_(updated_status, [
        ('tree0', 'closed', 'bomb damage'),
        ('tree1', 'closed', 'bomb damage'),
        ('tree2', 'closed', 'bug 456'),
    ])

    resp = client.get('/treestatus/stack')
    res = json.loads(resp.data)
    for st in res['result']:
        st['trees'].sort()
    eq_(res['result'], [{
        'id': 3,
        'trees': ['tree0', 'tree1'],
        'when': '2015-07-21T00:00:00+00:00',
        'who': 'human:user@domain.com',
        'reason': 'bomb damage',
        'status': 'closed',
    }, {
        'id': 2,
        'trees': ['tree1', 'tree2'],
        'when': '2015-07-16T00:00:00+00:00',
        'who': 'dustin',
        'reason': 'bug 456',
        'status': 'closed',
    }, {
        'id': 1,
        'trees': ['tree0', 'tree1'],
        'who': 'dustin',
        'when': '2015-07-14T00:00:00+00:00',
        'reason': 'bug 123',
        'status': 'closed',
    }
    ])

    assert_logged(app, 'tree0', 'closed', 'bomb damage', tags=['c4'])
    assert_logged(app, 'tree1', 'closed', 'bomb damage', tags=['c4'])
    assert_change_last_state(app, 3,
                             tree0=('closed', 'bug 123'),
                             tree1=('closed', 'bug 456'))
