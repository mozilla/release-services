import os

from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware
from relengapi_common import create_apps


NOAPP = object()
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.environ.get('APP', NOAPP)
RELENGAPI_SETTINGS = os.path.join(HERE, 'settings.py')

APPS = [
    'relengapi_clobberer',
    'shipit',
]

if not os.environ.get('RELENGAPI_SETTINGS') and \
        os.path.isfile(RELENGAPI_SETTINGS):
    os.environ['RELENGAPI_SETTINGS'] = RELENGAPI_SETTINGS
    if __name__ == '__main__' and not os.environ.get('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'sqlite:////%s/app.db' % HERE


if APP == NOAPP:
    apps = {
        '/__api__/' + app:  getattr(__import__(app), 'app')
        for app in APPS
    }
    app = DispatcherMiddleware(create_apps(__name__), apps)
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
