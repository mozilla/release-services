# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime as _datetime
import importlib
import pytz
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

class datetime():
    class datetime(_datetime.datetime):
        @classmethod
        def utcnow(cls):
            return _datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        @classmethod
        def utcfromtimestamp(cls, timestamp):
            return _datetime.datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.UTC)
    # The following are just pointers to facilitate code sanity
    date = _datetime.date
    time = _datetime.time
    timedelta = _datetime.timedelta
    tzinfo = _datetime.tzinfo
def dt_as_timezone(obj, dest_tzinfo):
    if not issubclass(obj, _datetime):
        raise ValueError("Must pass a datetime object")
    if obj.tzinfo is None:
        raise ValueError("Must pass a timezone aware datetime object")
    return dest_tzinfo.normalize(obj.astimezone(dest_tzinfo))