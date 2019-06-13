# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import copy

import jsone
import requests
import slugid

from cli_common.log import get_logger
from cli_common.taskcluster import get_service
from shipit_api.config import SUPPORTED_FLAVORS
from shipit_api.release import is_rc

log = get_logger(__name__)


class UnsupportedFlavor(Exception):
    def __init__(self, description):
        self.description = description


class ActionsJsonNotFound(Exception):
    pass


def get_trust_domain(project):
    if 'comm' in project:
        return 'comm'
    else:
        return 'gecko'


def find_decision_task_id(project, revision):
    decision_task_route = f'{get_trust_domain(project)}.v2.{project}.revision.{revision}.taskgraph.decision'
    index = get_service('index')
    return index.findTask(decision_task_route)['taskId']


def fetch_actions_json(task_id):
    try:
        queue = get_service('queue')
        actions_url = queue.buildUrl('getLatestArtifact', task_id, 'public/actions.json')
        q = requests.get(actions_url)
        q.raise_for_status()
        return q.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise ActionsJsonNotFound
        raise


def find_action(name, actions):
    for action in actions['actions']:
        if action['name'] == name:
            return copy.deepcopy(action)
    else:
        return None


def extract_our_flavors(avail_flavors, product, version, partial_updates, product_key=None):
    if not product_key:
        product_key = product

    if is_rc(version, partial_updates):
        product_key = f'{product_key}_rc'

    # sanity check
    all_flavors = set([fl['name'] for fl in SUPPORTED_FLAVORS[product_key]])
    if not set(avail_flavors).issuperset(all_flavors):
        description = f'Some flavors are not in actions.json: {all_flavors.difference(set(avail_flavors))}.'
        raise UnsupportedFlavor(description=description)
    return SUPPORTED_FLAVORS[product_key]


def generate_action_task(decision_task_id, action_name, input_, actions):
    target_action = find_action(action_name, actions)
    context = copy.deepcopy(actions['variables'])  # parameters
    action_task_id = slugid.nice()
    context.update({
        'input': input_,
        'taskGroupId': decision_task_id,
        'ownTaskId': action_task_id,
        'taskId': None,
        'task': None,
    })
    action_task = copy.deepcopy(target_action['task'])
    log.info('TASK: %s', action_task)
    return action_task_id, action_task, context


def render_action_task(task, context):
    action_task = jsone.render(task, context)
    return action_task


def generate_action_hook(task_group_id, action_name, actions, input_):
    target_action = find_action(action_name, actions)
    context = copy.deepcopy(actions['variables'])  # parameters
    context.update({
        'taskGroupId': task_group_id,
        'taskId': None,
        'task': None,
        'input': input_,
    })
    return dict(
        hook_group_id=target_action['hookGroupId'],
        hook_id=target_action['hookId'],
        hook_payload=target_action['hookPayload'],
        context=context,
    )


def render_action_hook(payload, context, delete_params=[]):
    rendered_payload = jsone.render(payload, context)
    # some parameters contain a lot of entries, so we hit the payload
    # size limit. We don't use this parameter in any case, safe to
    # remove
    for param in delete_params:
        del rendered_payload['decision']['parameters'][param]
    return rendered_payload
