'use strict';

require('expose-loader?jQuery!jquery');
require('expose-loader?Tether!tether');
require('bootstrap');
require('./scss/index.scss');

var redirect = require('./redirect');
var localstorage = require('./localstorage');
var hawk = require('./hawk');

var TC_KEY = 'taskclusterlogin';
var BZ_KEY = 'bugzillalogin';

// Load url from process (dev) or html element (staging/prod)
var getUrl = function(name, _default){
  var nameElt= 'data-' + name + '-url';
  var nameEnv = 'WEBPACK_' + name.toUpperCase() + '_URL';
  var url = document.body.getAttribute(nameElt);
  if(url)
    return url;
  return _default || "You need to set " + nameEnv + "variable or " + nameElt;
};

// Start the ELM application
var app = require('./Main.elm').Main.fullscreen({
  taskcluster: localstorage.load_item(TC_KEY),
  bugzilla: localstorage.load_item(BZ_KEY),
  backend_uplift_url: getUrl('uplift', process.env.WEBPACK_UPLIFT_URL),
  bugzilla_url: getUrl('bugzilla', process.env.WEBPACK_BUGZILLA_URL),
});

// Setup ports
localstorage.init(app, TC_KEY);
localstorage.init(app, BZ_KEY);
hawk(app);
redirect(app);
