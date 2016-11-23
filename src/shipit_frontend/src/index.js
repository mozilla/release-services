'use strict';

require('expose?$!expose?jQuery!jquery');
require('expose?Tether!tether');
require('bootstrap');
require("./index.scss");

var redirect = require('redirect.js');
var localstorage = require('localstorage.js');
var hawk = require('hawk.js');

var url;
var getUrl = function(name, _default) {
  url = document.body.getAttribute('data-' + name + '-url');
  if (url === null) {
    url = _default || 'You need to set NEO_' + name.toUperCase() + '_URL variable or data-' + name + '-url';
  }
  return url;
};

// Start the ELM application
var app = require('./Main.elm').Main.fullscreen({
  backend_dashboard_url: getUrl('dashboard', process.env.NEO_DASHBOARD_URL),
  bugzilla_url: getUrl('bugzilla', process.env.NEO_BUGZILLA_URL)
});

// Setup ports
localstorage(app, 'bugzillalogin');
localstorage(app, 'taskclusterlogin');
hawk(app);
redirect(app)
