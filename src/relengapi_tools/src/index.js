'use strict';

require('expose?$!expose?jQuery!jquery');
require('expose?Tether!tether');
require('bootstrap');
require("./index.scss");

var user = null;
try {
  user = JSON.parse(window.localStorage.getItem('relengapi-credentials'));
} catch (e) {
  console.log(e);
}

console.log(user);
var url = require('url');
var app = require('./Main.elm').Main.fullscreen({
  user: user
});
    

app.ports.clear_credentials.subscribe(function() {
    window.localStorage.removeItem('relengapi-credentials');
    app.ports.load_credentials.send(null);
});

app.ports.save_credentials.subscribe(function(user) {
    window.localStorage.setItem('relengapi-credentials', JSON.stringify(user));
    console.log(user);
    app.ports.load_credentials.send(user);
});

app.ports.redirect.subscribe(function(redirect) {
   var redirect_url = url.parse(redirect.url);
   if (redirect.target !== null) {
     redirect_url = url.format($.extend({}, redirect_url, {
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
