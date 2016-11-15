'use strict';

require('expose?$!expose?jQuery!jquery');
require('expose?Tether!tether');
require('bootstrap');
require("./index.scss");
require('./user');

var KEY = 'taskcluster-login';
var user = null;

try {
  user = JSON.parse(window.localStorage.getItem(KEY));
} catch (e) {
  // pass
}

var treestatusUrl = document.body.getAttribute('data-treestatus-url');
if (treestatusUrl === null) {
  treestatusUrl = process.env.NEO_TREESTATUS_URL || "You need to set NEO_TREESTATUS_URL variable or data-treestatus-url";
}

var app = require('./Main.elm').Main.fullscreen({
  user: user,
  treestatusUrl: treestatusUrl 
});
    

window.app_user(app, KEY);
