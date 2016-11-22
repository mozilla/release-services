'use strict';

require('expose?$!expose?jQuery!jquery');
require('bootstrap/dist/css/bootstrap.css');

var redirect = require('redirect.js');
var localstorage = require('localstorage.js');
var hawk = require('hawk.js');

// Start the ELM application
var app = require('./Main.elm').Main.fullscreen({
  bugzilla_url: 'https://bugzilla-dev.allizom.org',
});

// Setup ports
localstorage(app, 'bugzillalogin');
localstorage(app, 'taskclusterlogin');
hawk(app);
redirect(app);
