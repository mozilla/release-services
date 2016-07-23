'use strict';

require('expose?$!expose?jQuery!jquery');
require('expose?Tether!tether');
require('bootstrap');
require("./index.scss");

var url = require('url');

var user = null;
try {
  user = JSON.parse(window.localStorage.getItem('relengapi-credentials'));
} catch (e) {
  console.log(e);
}

var clobbererUrl = document.body.getAttribute('data-clobberer-url');
if (clobbererUrl === null) {
    clobbererUrl = url.format({
        protocol: window.location.protocol,
        host: window.location.host,
        port: window.location.port
    });
}

var app = require('./Main.elm').Main.fullscreen({
  user: user,
  clobbererUrl: clobbererUrl
});
    

app.ports.localstorage_remove.subscribe(function() {
    debugger
    window.localStorage.removeItem('relengapi-credentials');
    app.ports.localstorage_get.send(null);
});

app.ports.localstorage_set.subscribe(function(user) {
    debugger
    window.localStorage.setItem('relengapi-credentials', JSON.stringify(user));
    app.ports.localstorage_get.send(user);
});

app.ports.redirect.subscribe(function(redirect) {
    debugger
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
