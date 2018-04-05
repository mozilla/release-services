# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


def create_app(config=None):
    import os
    import backend_common
    import shipit_uplift.config
    import shipit_uplift.models  # noqa

    app = backend_common.create_app(
        app_name=shipit_uplift.config.APP_NAME,
        project_name=shipit_uplift.config.PROJECT_NAME,
        config=config,
        extensions=[
            'log',
            'security',
            'cors',
            'api',
            'auth',
            'db',
            'cache',
        ],
    )
    # TODO: add predefined api.yml
    app.api.register(os.path.join(os.path.dirname(__file__), 'api.yml'))
    return app
