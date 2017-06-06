'use strict';

require('expose-loader?jQuery!jquery');
require('expose-loader?Tether!tether');
require('bootstrap');
require('./scss/index.scss');

var url;
var getData = function(name, _default) {
  url = document.body.getAttribute('data-' + name);
  if (url === null) {
    url = _default;
  }
  if (url === undefined) {
    throw Error('You need to set `data-' + name + '`');
  }
  return url;
};

var redirect = require('./redirect');
var localstorage = require('./localstorage');
var hawk = require('./hawk');

var release_version = getData('release-version', process.env.RELEASE_VERSION)
var release_channel = getData('release-channel', process.env.RELEASE_CHANNEL);

var TC_KEY = 'taskclusterlogin';  // do not change this key

var init = function() {
    // Start the ELM application
    var app = require('./Main.elm').Main.fullscreen({
      user: localstorage.load_item(TC_KEY),
      treestatusUrl: getData('releng-treestatus-url', process.env.RELENG_TREESTATUS_URL),
      docsUrl: getData('releng-docs-url', process.env.RELENG_DOCS_URL),
      version: release_version
    });


    // Setup ports
    localstorage.init(app, KEY);
    hawk(app);
    redirect(app);
    title(app);
};

// Setup logging
var Raven = require('raven-js');
var sentry_dsn = document.body.getAttribute('data-sentry-dsn');
if (sentry_dsn != null) {
    Raven
        .config(
            sentry_dsn,
            {
                debug: true,
                release: release_version,
                environment: release_channel,
                tags: {
                    server_name: 'mozilla-releng/services',
                    site: 'releng-frontend'
                }
            })
        .install()
        .context(init);
} else {
    init();
}
