from setuptools import setup, find_packages

setup(
    name='relengapi',
    version='0.0',
    description='The code behind https://api.pub.build.mozilla.org',
    author='Dustin J. Mitchell',
    author_email='dustin@mozilla.com',
    url='https://api.pub.build.mozilla.org',
    install_requires=[
        "Flask",
        "Flask-OAuthlib",
        "Flask-Login",
        "Flask-Browserid",
        "SQLAlchemy",
        "Celery",
    ],
    tests_require=["nose", "mock"],
    packages=find_packages(),
    include_package_data=True,
    test_suite='nose.collector',
    namespace_packages=['relengapi', 'relengapi.blueprints'],
    entry_points={
        "relengapi_blueprints": [
            'base = relengapi.blueprints.base:bp',
            'oauth = relengapi.blueprints.oauth:bp',
            'userauth = relengapi.blueprints.userauth:bp',
        ],
        "console_scripts": [
            'relengapi = relengapi.subcommands:main',
        ],
    },
)
