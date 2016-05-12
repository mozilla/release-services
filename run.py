import os

from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware
from relengapi_common import create_app_list


MARKER = object()
HERE = os.path.dirname(__file__)
APP = os.environ.get('APP', MARKER)
APPS = os.listdir(os.path.join(HERE, 'src'))
APPS = filter(lambda x: os.path.isfile(os.path.join('src', x, 'requirements.txt')), APPS)  # noqa
APPS = map(lambda x: x.lstrip('relengapi_'), APPS)
RELENGAPI_SETTINGS = os.path.join(HERE, 'settings.py')

if not os.environ.get('RELENGAPI_SETTINGS') and \
        os.path.isfile(RELENGAPI_SETTINGS):
    os.environ['RELENGAPI_SETTINGS'] = RELENGAPI_SETTINGS

if APP == MARKER:
    apps = {'/' + app:  getattr(__import__('relengapi_' + app), 'app') for app in APPS}  # noqa
    app = DispatcherMiddleware(create_app_list(__name__, APPS), apps)
    if __name__ == '__main__':
        for app_ in apps.values():
            app_.debug = True
else:
    app = getattr(__import__('relengapi_' + APP), 'app')


if __name__ == '__main__':
    if hasattr(app, 'run'):
        app.run(debug=True)
    else:
        run_simple('localhost', 5000, app,
                   use_reloader=True, use_debugger=True, use_evalex=True)
