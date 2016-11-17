# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from copy import copy
import requests


class PipelineStep:
    def __init__(self, uid, url, params, requires, state):
        self.uid = uid
        self.url = url
        self.params = params
        self.requires = requires
        self.state = state

    def __copy__(self):
        new = self.__class__(uid=self.uid, url=self.url, params=self.params,
                             requires=self.requires, state=self.state)
        return new

    @classmethod
    def update_state(cls, step):
        new = copy(step)
        new.state = step.get_state()
        return new

    def get_state(self):
        return requests.get(self.url).json()

    def get_next_steps(self, pipeline):
        return [step for step in pipeline if self.uid in step.requires]

# e.g.
# s1 = PipelineStep.update_state(s0)


def refresh_pipeline_steps(pipeline):
    retval = []
    for step in pipeline:
        state = step.state
        if state in ('running',):
            state = step.get_state()
        retval.append(PipelineStep(step.uid, step.url, step.params,
                                   step.requires, state))
    return retval


def get_runnable_steps(pipeline):
    states = {step.uid: step.state for step in pipeline}

    retval = []
    for step in pipeline:
        if all(states[r.uid] == 'completed' for r in step.requires):
            retval.append(step)
    return retval
