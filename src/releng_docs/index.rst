Mozilla Release Engineering Services
====================================

A highlevel goal of *Release Engineering Services* is to **converge efforts**
to develop, test, maintain and *most importantly* document services that
*Release Engineering Team* is providing.

Currently supported platform is **Linux**. In the future we could think of also
supporting OSX (Darwin) as development platform, but initial efforts are on
purpose kept as small as possible.

TODO: explain why we want to converge efforts?
TODO: why mono-repository approach?
TODO: why a single version? why not semver?

:code: https://github.com/mozilla-releng/services
:issues: https://github.com/mozilla-releng/services/issues


Repository structure
--------------------

- ``CONTRIBUTE.rst`` A contribution guide used by github.
- ``LICENSE.txt`` license of code (Mozilla Public License Version 2.0).
- ``Makefile`` Few helper commands (gnumake required).
- ``README.rst`` A short description of the project (eg. quickstart).
- ``VERSION`` A version of all projects
- ``contribute.json`` A JSON schema for open-source project contribution data. https://www.contributejson.org/
- ``src/`` A folder where all projects are placed, described bellow.
- ``nix/`` A build (Nix) related tools, scripts, etc... :ref:`more <build-process>`


.. _build-process

Build process
-------------

TODO: find better title








Replace ``<project>`` with one of folder names from ``./src``. 


To run tests and build a project::

    nix-build nix/default.nix -A <project>

To enter development mode::

    nix-shell nix/default.nix -A <project>


.. toctree::
    :maxdepth: 2

    service/clobberer 

