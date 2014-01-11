from setuptools import setup, find_packages

setup(
    name='relengapi-kron',
    version='0.0',
    description='Documentation blueprint for relengapi',
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
            'kron = relengapi.blueprints.kron:bp',
        ],
    },
)
