'use strict';

require('expose?$!expose?jQuery!jquery');
require('expose?Tether!tether');
require('bootstrap');
require('./index.scss');

var redirect = require('./redirect');
var localstorage = require('./localstorage');
var hawk = require('./hawk');

var url;
var getUrl = function(name, _default) {
  url = document.body.getAttribute('data-' + name + '-url');
  if (url === null) {
    url = _default || 'You need to set NEO_' + name.toUperCase() + '_URL variable or data-' + name + '-url';
  }
  return url;
};

var KEY = 'taskclusterlogin';  // do not change this key
var user = null;
try {
  user = JSON.parse(window.localStorage.getItem(KEY));
} catch (e) {
  // pass
}

// Start the ELM application
var app = require('./Main.elm').Main.fullscreen({
  user: user,
  treestatusUrl: getUrl('treestatus', process.env.NEO_TREESTATUS_URL)
});

// Setup ports
localstorage(app, KEY);
hawk(app);
redirect(app);
