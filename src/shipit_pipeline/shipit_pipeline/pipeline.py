# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from copy import copy
import requests


class PipelineStep:
    def __init__(self, uid, url, params, requires, state=None):
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
        return requests.get(self.url).json()['state']

    def get_next_steps(self, pipeline):
        return [step for step in pipeline if self.uid in step.requires]

    @property
    def is_runnable(self):
        return self.state is None


def refresh_pipeline_steps(pipeline):
    retval = []
    for step in pipeline:
        state = step.state
        if state in ('running',):
            step = step.update_state()

        retval.append(step)
    return retval


def get_runnable_steps(pipeline):
    states = {step.uid: step.state for step in pipeline}

    return [step for step in pipeline if all(states[r] == 'completed' for r in step.requires) and step.is_runnable]
