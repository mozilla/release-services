'use strict';

require('expose?$!expose?jQuery!jquery');
require('bootstrap/dist/css/bootstrap.css');

var redirect = require('./redirect');
var localstorage = require('./localstorage');
var hawk = require('./hawk');

// Start the ELM application
var app = require('./Main.elm').Main.fullscreen();

// Setup ports
localstorage(app, 'bugzillalogin');
localstorage(app, 'taskclusterlogin');
hawk(app);
redirect(app);
