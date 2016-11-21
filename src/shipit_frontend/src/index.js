'use strict';

require('expose?$!expose?jQuery!jquery');
require('expose?Tether!tether');
require('bootstrap');
require("./index.scss");

var redirect = require('redirect.js');
var localstorage = require('localstorage.js');
var hawk = require('hawk.js');

// Load backends url from process (dev) or html element (staging/prod)
var backend_dashboard_url = document.body.getAttribute('data-dashboard-url');
if (backend_dashboard_url === null) {
  backend_dashboard_url = process.env.NEO_DASHBOARD_URL || "You need to set NEO_DASHBOARD_URL variable or data-dashboard-url";
}
var bugzilla_url = document.body.getAttribute('data-bugzilla-url');
if (bugzilla_url === null) {
  bugzilla_url = process.env.NEO_BUGZILLA_URL || "You need to set NEO_BUGZILLA_URL variable or data-bugzilla-url";
}

// Start the ELM application
var app = require('./Main.elm').Main.fullscreen({
  backend_dashboard_url: backend_dashboard_url,
  bugzilla_url: bugzilla_url
});

// Setup ports
localstorage(app, 'bugzillalogin');
localstorage(app, 'taskclusterlogin');
hawk(app);
redirect(app);
