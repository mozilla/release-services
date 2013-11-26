from setuptools import setup, find_packages

setup(
    name='releng-api',
    version='0.0',
    description='The One True API',
    author='Dustin J. Mitchell',
    author_email='dustin@mozilla.com',
    url='',
    install_requires=[
        "Flask",
    ],
    tests_require=["nose", "mock"],
    packages=find_packages(),
    include_package_data=True,
    test_suite='nose.collector',
    entry_points={
        "console_scripts": [
            'releng_api = releng_api.scripts.server:main',
        ]
    },
)
