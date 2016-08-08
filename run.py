import os

from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware
from relengapi_common import create_apps, create_app


NOAPP = object()
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.environ.get('APP', NOAPP)
RELENGAPI_SETTINGS = os.path.join(HERE, 'settings.py')
DEBUG = __name__ == '__main__'
HOST = os.environ.get('HOST', 'localhost')
PORT = int(os.environ.get('PORT', '5000'))

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

extra_files = []


def run_app(app_name, app_url):
    app_path = os.path.join(HERE, 'src', app_name)
    app_extensions = getattr(__import__(app_name), 'extensions', [])
    app_init = getattr(__import__(app_name), 'init_app')

    if DEBUG:
        os.environ['{}_BASE_URL'.format(app_name.upper())] = app_url

    app_extensions.append(app_init)

    app = create_app(app_name, extensions=app_extensions, debug=DEBUG)

    print('Serving "{}" on: {}'.format(app_name, app_url or "/"))

    for base, dirs, files in os.walk(app_path):
        for file in files:
            if file.endswith(".yml"):
                extra_files.append(os.path.join(base, file))
    return app


if APP == NOAPP:
    apps = {}
    for app_name in APPS:
        app_url = '/__api__/' + ('/'.join(app_name.split('_')))
        apps[app_url] = run_app(app_name, app_url)
    app = DispatcherMiddleware(create_apps(__name__, debug=DEBUG), apps)
else:
    app = run_app(APP, "")


werkzeug_options = dict(
    use_reloader=DEBUG,
    use_debugger=DEBUG,
    use_evalex=DEBUG,
    extra_files=extra_files,
)


if __name__ == '__main__':
    if hasattr(app, 'run'):
        app.run(
            host=HOST,
            port=PORT,
            debug=DEBUG,
            **werkzeug_options
        )
    else:
        run_simple(
            hostname=HOST,
            port=PORT,
            application=app,
            **werkzeug_options
        )
