# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time
from copy import copy

import requests


class PipelineStep:
    def __init__(self, uid, url, params, requires, state='pending'):
        self.uid = uid
        self.url = url
        self.params = params
        self.requires = requires
        self.state = state

    def __copy__(self):
        new = self.__class__(uid=self.uid, url=self.url, params=self.params,
                             requires=self.requires, state=self.state)
        return new

    def __repr__(self):
        return str(self.__dict__)

    @classmethod
    def from_dict(cls, dict_):
        # TODO validate params against schema?
        return cls(uid=dict_['uid'], url=dict_['api_url'], params=dict_['parameters'], requires=dict_['requires'])

    def update_state(self):
        new = copy(self)
        new.state = self.get_state()
        return new

    def get_state(self):
        return requests.get('{}/status'.format(self.full_url), verify=False).json()['state']

    def get_next_steps(self, steps):
        return [step for step in steps if self.uid in step.requires]

    @property
    def full_url(self):
        return '{}/{}'.format(self.url, self.uid)

    @property
    def is_pending(self):
        return self.state == 'pending'

    @property
    def is_running(self):
        return self.state in ('starting', 'running')


class MockPipelineStep:
    MockSteps = {}

    def __init__(self, uid, params, requires, state='pending', step_time=100):
        self.uid = uid
        self.url = ''
        self.params = params
        self.requires = requires
        self.state = state
        self.step_time = step_time

    def start_step(self, uid, data, verify):
        self.start_time = time.time()

    def complete(self):
        self.state = 'completed'

    def get_state(self):
        current_time = time.time()
        if current_time - self.start_time > self.step_time:
            return 'completed'
        return self.state

    def update_state(self):
        if self.current_time - self.start_time > self.step_time:
            self.state = 'completed'

    @property
    def is_pending(self):
        return self.state == 'pending'

    @property
    def is_running(self):
        return self.state in ('starting', 'running')

    @property
    def full_url(self):
        return '{}/mock/{}'.format(self.url, self.uid)

    def to_dict(self):
        return {
                  'parameters': {
                    'api_url': self.full_url,
                    'description': 'string',
                    'parameters': self.params,
                    'parameters_schema': 'string',
                    'requires': [
                      self.requires
                    ],
                    'uid': self.uid
                  },
                  'uid': self.uid
                }


def refresh_pipeline_steps(steps):
    retval = []
    for step in steps:
        if step.is_running:
            step = step.update_state()

        retval.append(step)
    return retval


def get_runnable_steps(steps):
    states = {step.uid: step.state for step in steps}
    return [step for step in steps if all(states[r] == 'completed' for r in step.requires) and step.is_pending]


def get_running_steps(steps):
    return [step for step in steps if step.is_running]


def start_steps(steps):
    for step in steps:
        response = requests.put(step.full_url, data=step.params, verify=False)
        response.raise_for_status()
        # TODO: Find a better name for step.update_state
        # TODO handle errors
        step.state = 'starting'
