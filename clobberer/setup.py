from setuptools import setup, find_packages

setup(
    name='relengapi-clobberer',
    version='0.0',
    description='RelengAPI blueprint for interfacing with clobberer',
    author='Dustin J. Mitchell',
    author_email='dustin@mozilla.com',
    url='',
    install_requires=[
        "Flask",
        "relengapi",
    ],
    tests_require=["nose", "mock"],
    packages=find_packages(),
    include_package_data=True,
    test_suite='nose.collector',
    namespace_packages=['relengapi.blueprints'],
    entry_points={
        "relengapi_blueprints": [
            'clobberer = relengapi.blueprints.clobberer:bp',
        ],
    },
)
