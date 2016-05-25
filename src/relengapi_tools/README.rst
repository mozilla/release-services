===============
RelengAPI Tools
===============

TODO: what this app is for, list useful links

Tools used in this project:

- react
- immutable
- redux
- redux-router
- bootstrap (v4)


Commands
========

- ``npm run dev``

    Run development instance of application, on http://localhost:8080,
    via `webpack-dev-server`_, with hot reloading of code via
    `webpack hot module reload`_.

- ``npm run build``

    Build production ready static files into ``./build`` folder.

- ``npm run test``

    Run all the tests for the project one time.

    Coverage can be found in ``./coverage`` folder.

- ``npm run test:dev``

    Open browser, then run all tests, keep browser open and listen for code
    changes, then rerun the tests.

    Coverage can be found in ``./coverage`` folder.


Configuration
=============

This project does not use any of the *traditional* javascript building tools
(eg. `Gulp`_, `Grunt`_). It connects all with `webpack`_ and different webpack
loaders. Webpack is used here because it also provides nice development
environment (hot reload of code). Configuration for development, testing and
production can be found in ``./webpack.config.js``.

Webpack hooks and applies this `babel`_ transforms:
- `babel-preset-es2015`_
- `babel-preset-react`_
- `babel-preset-stage-0`_

Configuration for `eslint`_ configuration, which is used in webpack's build
chain is configured in ``./packages.json``, since this is the location eslint
linter looks.

For testing, test runner `karma`_ is used. It used webpack's configuration to
apply all babel transforms and runs tests in for different browsers.
Configuration for karma can be found in ``./karma.conf.js``


Deploying
=========

TODO: ask dustin how setup ssl and deploy taskcluster docs to s3


.. _`webpack-dev-server`: https://www.npmjs.com/package/webpack-dev-server
.. _`webpack hot module reload`: http://webpack.github.io/docs/hot-module-replacement-with-webpack.html
.. _`Gulp`: http://gulpjs.com/
.. _`Grunt`: http://gruntjs.com/
.. _`webpack`: http://webpack.github.io/
.. _`karma`: https://karma-runner.github.io/
.. _`babel`: http://babeljs.io/
.. _`eslint`: http://eslint.org/
.. _`babel-preset-es2015`: http://babeljs.io/docs/plugins/preset-es2015/
.. _`babel-preset-react`: http://babeljs.io/docs/plugins/preset-react/
.. _`babel-preset-stage-0`: http://babeljs.io/docs/plugins/preset-stage-0/

todo:
    https://pageshot.dev.mozaws.net/
    https://mozilla.github.io/mozmaker/demo/
    https://github.com/mozilla/tabzilla

    https://github.com/xgrommx/awesome-redux
    https://github.com/reactjs/reselect
    http://indexiatech.github.io/re-notif/
    https://github.com/michaelcontento/redux-storage

    https://github.com/raisemarketplace/redux-loop
    http://yelouafi.github.io/redux-saga/
    http://redux.js.org/docs/advanced/Middleware.html
    http://redux.js.org/docs/advanced/ExampleRedditAPI.html
    http://yelouafi.github.io/redux-saga/docs/basics/ErrorHandling.html

    https://auth0.com/blog/2016/01/04/secure-your-react-and-redux-app-with-jwt-authentication/
