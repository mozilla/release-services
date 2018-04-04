# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import copy
import jsone
import requests
import slugid
import taskcluster
from shipit_workflow.release import is_rc
from cli_common.log import get_logger

log = get_logger(__name__)

# Phases per product, ordered
SUPPORTED_FLAVORS = {
    'firefox': ['promote_firefox', 'push_firefox', 'ship_firefox'],
    'firefox_rc': ['promote_firefox_rc', 'ship_firefox_rc', 'push_firefox', 'ship_firefox'],
    'fennec': ['promote_fennec', 'ship_fennec'],
    'fennec_rc': ['promote_fennec', 'ship_fennec_rc', 'ship_fennec'],
    'devedition': ['promote_devedition', 'push_devedition', 'ship_devedition'],
}


def find_decision_task_id(project, revision):
    decision_task_route = 'gecko.v2.{project}.revision.{revision}.firefox.decision'.format(
         project=project, revision=revision)
    index = taskcluster.Index()
    return index.findTask(decision_task_route)['taskId']


def fetch_actions_json(task_id):
    queue = taskcluster.Queue()
    actions_url = queue.buildUrl('getLatestArtifact', task_id, 'public/actions.json')
    q = requests.get(actions_url)
    q.raise_for_status()
    return q.json()


def find_action(name, actions):
    for action in actions['actions']:
        if action['name'] == name:
            return copy.deepcopy(action)
    else:
        return None


def extract_our_flavors(avail_flavors, product, version, partial_updates):
    # sanity check
    all_flavors = set([fl for product in SUPPORTED_FLAVORS.keys() for fl in SUPPORTED_FLAVORS[product]])
    if sorted(all_flavors) != sorted(set(avail_flavors)):
        raise Exception('Some flavors are not supported {} vs {}'.format(all_flavors, set(avail_flavors)))
    if is_rc(version, partial_updates):
        key = '_rc'.format(product)
    else:
        key = product
    our_flavors = [fl for fl in avail_flavors if fl in SUPPORTED_FLAVORS[key]]
    # sort the phases by their appearance in SUPPORTED_FLAVORS
    return sorted(our_flavors, key=SUPPORTED_FLAVORS[key].index)


def generate_action_task(action_task_input, actions):
    relpro = find_action('release-promotion', actions)
    context = copy.deepcopy(actions['variables'])  # parameters
    action_task_id = slugid.nice().decode('utf-8')
    context.update({
        'input': action_task_input,
        'ownTaskId': action_task_id,
        'taskId': None,
        'task': None,
    })
    action_task = copy.deepcopy(relpro['task'])
    log.info('TASK: %s', action_task)
    return action_task_id, action_task, context


def render_action_task(task, context, action_task_id):
    action_task = jsone.render(task, context)
    # override ACTION_TASK_GROUP_ID, so we know the new ID in advance
    action_task['payload']['env']['ACTION_TASK_GROUP_ID'] = action_task_id
    return action_task
