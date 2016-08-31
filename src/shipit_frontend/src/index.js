'use strict';

require('expose?$!expose?jQuery!jquery');
require('expose?Tether!tether');
require('bootstrap');
require("./index.scss");

var backend_url = process.env.NEO_DASHBOARD_URL || "http://localhost:5000";
console.info('Dashboard backend used ', backend_url);

// Load credentials
var user = null;
try {
  user = JSON.parse(window.localStorage.getItem('shipit-credentials'));
  user = user.value || user;
  console.info('Loaded user', user);
} catch (e) {
  console.warn('Loading user failed', e);
}

// Start the ELM application
var url = require('url');
var app = require('./Main.elm').Main.fullscreen({
  user: user,
  backend_url: backend_url
});

// Local storage ports
app.ports.localstorage_remove.subscribe(function() {
  window.localStorage.removeItem('shipit-credentials');
  app.ports.localstorage_get.send(null);
});

app.ports.localstorage_set.subscribe(function(user) {
  user = user ? user.value : null;
  window.localStorage.setItem('shipit-credentials', JSON.stringify(user));
  app.ports.localstorage_get.send(user);
});

app.ports.redirect.subscribe(function(redirect) {
   var redirect_url = url.parse(redirect.url);
   if (redirect.target !== null) {
     redirect_url = url.format(window.$.extend({}, redirect_url, {
       query: {
         target: url.format({
             protocol: window.location.protocol,
             host: window.location.host,
             port: window.location.port,
             pathname: redirect.target[0]
         }),
         description: redirect.target[1]
       }
     }));
   } else {
     redirect_url = url.format(redirect_url)
   }
   window.location = redirect_url;
});
