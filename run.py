import os

from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware
from relengapi_common import create_apps, create_app


NOAPP = object()
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.environ.get('APP', NOAPP)
RELENGAPI_SETTINGS = os.path.join(HERE, 'settings.py')
DEBUG = __name__ == '__main__'

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
        app_extensions = getattr(__import__(app_name), 'extensions', [])
        app_init = getattr(__import__(app_name), 'init_app')

        app_extensions.append(app_init)
        app = create_app(app_name, extensions=app_extensions, debug=DEBUG)

        print('Serving "{}" on: {}'.format(app_name, app_path))

        apps[app_path] = app
        os.environ['{}_BASE_URL'.format(app_name.upper())] = \
            'http://localhost:5000' + app_path

    app = DispatcherMiddleware(create_apps(__name__, debug=DEBUG), apps)

else:
    app_name = APP
    app_extensions = getattr(__import__(APP), 'extensions')
    app = create_app(app_name, extensions=app_extensions, debug=DEBUG)


if __name__ == '__main__':
    if hasattr(app, 'run'):
        app.run(debug=DEBUG)
    else:
        run_simple('localhost', 5000, app,
                   use_reloader=DEBUG, use_debugger=DEBUG, use_evalex=DEBUG)
