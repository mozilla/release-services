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
        "Flask-SQLAlchemy",
    ],
    tests_require=["nose", "mock"],
    packages=find_packages(),
    include_package_data=True,
    test_suite='nose.collector',
    namespace_packages=['relengapi.blueprints'],
    entry_points={
        "console_scripts": [
            'relengapi = relengapi.scripts.base:main',
        ],
    },
)
