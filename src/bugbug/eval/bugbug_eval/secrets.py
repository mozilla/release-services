# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from bugbug_eval import config
from cli_common.taskcluster import get_secrets


class Secrets(dict):
    APP_CHANNEL = 'APP_CHANNEL'
    BUGZILLA_TOKEN = 'BUGZILLA_TOKEN'

    def load(self, taskcluster_secret, taskcluster_client_id, taskcluster_access_token):
        secrets = get_secrets(
            taskcluster_secret,
            config.PROJECT_NAME,
            required=(
                Secrets.APP_CHANNEL,
                Secrets.BUGZILLA_TOKEN,
            ),
            taskcluster_client_id=taskcluster_client_id,
            taskcluster_access_token=taskcluster_access_token,
        )

        self.update(secrets)


secrets = Secrets()
