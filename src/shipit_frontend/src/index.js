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

var TC_KEY = 'taskclusterlogin';
var BZ_KEY = 'bugzillalogin';

var init = function() {

    // Start the ELM application
    var app = require('./Main.elm').Main.fullscreen({
      taskcluster: localstorage.load_item(TC_KEY),
      bugzilla: localstorage.load_item(BZ_KEY),
      backend_uplift_url: getData('shipit-uplift-url', process.env.SHIPIT_UPLIFT_URL),
      bugzilla_url: getData('bugzilla-url', process.env.BUGZILLA_URL),

      auth_domain: getData('auth-domain', process.env.AUTH_DOMAIN),
      auth_client_id: getData('auth-client-id', process.env.AUTH_CLIENT_ID),
    });

    // Setup ports
    localstorage.init(app, TC_KEY);
    localstorage.init(app, BZ_KEY);
    hawk(app);
    redirect(app);
}

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
