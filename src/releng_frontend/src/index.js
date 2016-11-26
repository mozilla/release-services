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
    url = _default || 'You need to set NEO_' + name.toUpperCase() + '_URL variable or data-' + name + '-url';
  }
  return url;
};


// Start the ELM application
var KEY = 'taskclusterlogin';  // do not change this key
var app = require('./Main.elm').Main.fullscreen({
  user: localstorage.load_item(KEY),
  treestatusUrl: getUrl('treestatus', process.env.NEO_TREESTATUS_URL)
});

// Setup ports
localstorage.init(app, KEY);
hawk(app);
redirect(app);
