Mozilla Release Engineering Services
====================================


A repository to converge development of different projects. Currently setup
offers:

- Flask + OpenAPI (Swagger) based framework to easily create JSON APIs
- Continuous integration with taskcluster
- Running tests for all your projects (python) dependencies
- Automatically updating requirements.txt (if all tests pass ofcourse)
- Building docker images for you projects
- Deployments to heroku / s3
- (Build) reproducible environements
- Binary cache (no more waiting for things to compile)
- (PLANNED) Automatically checking your project for potential vulnerabilities
  (CVE)

Currently supported platform is Linux. We could think of also supporting OSX
(Darwin), but that would require some effort, but it is possible.


:code: https://github.com/garbas/mozilla-releng


.. toctree::
    :maxdepth: 2

    service/clobberer 

