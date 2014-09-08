# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import types

# Replace the `relengapi.celery` module with a 'celery' property that will
# create a new Flask app and Celery app on demand.  This lets 'celery -A
# relengapi worker' work as expected.  See
# http://celery.readthedocs.org/en/latest/getting-started/next-steps.html#about-the-app-argument


class PropModule(types.ModuleType):

    @property
    def celery(self):
        import relengapi.app
        app = relengapi.app.create_app(True)
        return app.celery

old_module = sys.modules[__name__]
new_module = PropModule(__name__)
new_module.__dict__.update(old_module.__dict__)
sys.modules[__name__] = new_module
