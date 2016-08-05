import os

from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware
from relengapi_common import create_apps


NOAPP = object()
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.environ.get('APP', NOAPP)
RELENGAPI_SETTINGS = os.path.join(HERE, 'settings.py')

APPS = []
NOT_APPS = ['relengapi_common']

for app in os.listdir(os.path.join(HERE, 'src')):
    if os.path.isdir(os.path.join(HERE, 'src', app)) and \
       os.path.isfile(os.path.join(HERE, 'src', app, 'setup.py')) and \
       app not in NOT_APPS:
        APPS.append(app)

if not os.environ.get('RELENGAPI_SETTINGS') and \
        os.path.isfile(RELENGAPI_SETTINGS):
    os.environ['RELENGAPI_SETTINGS'] = RELENGAPI_SETTINGS
    if __name__ == '__main__' and not os.environ.get('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'sqlite:////%s/app.db' % HERE


if APP == NOAPP:

    apps = {}
    for app_name in APPS:
        app_path = '/__api__/' + ('/'.join(app_name.split('_')))
        app = getattr(__import__(app_name), 'app')

        print('Serving "{}" on: {}'.format(app_name, app_path))

        apps[app_path] = app
        os.environ['{}_BASE_URL'.format(app_name.upper())] = \
            'http://localhost:5000' + app_path

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
