# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import importlib
import wrapt

def synchronized(lock):
    @wrapt.decorator
    def wrap(wrapper, instance, args, kwargs):
        with lock:
            return wrapper(*args, **kwargs)
    return wrap

def make_support_class(app, module_path, mechanisms, config_key, default):
    mechanism = app.config.get(config_key, {}).get('type', default)
    try:
        module_name, class_name = mechanisms[mechanism]
    except KeyError:
        raise RuntimeError("no such %s type '%s'" % (config_key, mechanism))

    # stash this for easy access from the templates
    app.config[config_key + '_TYPE'] = mechanism

    mech_module = importlib.import_module(module_name, module_path)
    mech_class = getattr(mech_module, class_name)
    return mech_class(app)


