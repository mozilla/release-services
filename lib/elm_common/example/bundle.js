(function(){

  window.hawk = function(app){

    var port_name = 'hawk_add_header';
    if(!app.ports || !app.ports[port_name]){
      console.warn('Undefined ELM port', port_name);
      return;
    }

    app.ports[port_name].subscribe(function(settings, request, user){
      console.debug('In hawk_add_header');

/*
      // Build optional cert
      var extData = null;
      if(request.certificate)
        extData = new Buffer(JSON.stringify({certificate: request.certificate})).toString('base64');

      // Generic payload for both headers
      var payload = {
        credentials: {
          id: request.id,
          key: request.key,
          algorithm: 'sha256'
        },
        ext: extData,
      };

      // Build backend & target (optional) headers
      var backend = Hawk.client.header(request.backend.url, request.backend.method, payload);
      var target = null;
      if(request.target)
        target = Hawk.client.header(request.target.url, request.target.method, payload);
*/
      console.info('HAWK Request', settings, request, user);

      if(!request.headers)
          request.headers = [];
      request.headers.push(['Authorization', 'DEMO_AUTH']);

      // Send back headers
      app.ports.hawk_send_request.send(settings, request);
    });
  }
}());
(function() {

  // TODO: restore it
  //var url = require('url');

  var isObject = function(data) { typeof data === typeof {}; };

  var parse = function(data) {
    var out = null;
    try {
      out = JSON.parse(data);
      if (!out) {
        out = null;
      }
    } catch (e) {
      out = null;
    }
    return out;
  };

  console.log('Initializer local storage');
  window.localstorage = function(app, namespace) {

    var port_name = namespace + '_load';
    if(!app.ports || !app.ports[port_name]){
      console.warn('Undefined ELM port', port_name);
      return;
    }

    app.ports[port_name].subscribe(function() {
      app.ports[namespace + '_get'].send(parse(window.localStorage.getItem(namespace)));
    });

    var port_name = namespace + '_remove';
    if(!app.ports || !app.ports[port_name]){
      console.warn('Undefined ELM port', port_name);
      return;
    }

    app.ports[port_name].subscribe(function() {
      window.localStorage.removeItem(namespace);
      app.ports[namespace + '_get'].send(null);
    });

    var port_name = namespace + '_set';
    if(!app.ports || !app.ports[port_name]){
      console.warn('Undefined ELM port', port_name);
      return;
    }

    app.ports[port_name].subscribe(function(new_data) {
      var data = parse(window.localStorage.getItem(namespace));

      // Update without erasing other fields when data and new_data are objects
      if (isObject(data) && isObject(new_data)) {
        for (var property in new_data) {
          if (new_data.hasOwnProperty(property)) {
            data[property] = new_data[property];
          }
        }
      } else {
          data = new_data;
      }

      window.localStorage.setItem(namespace, JSON.stringify(data));
      app.ports[namespace + '_get'].send(data);
    });
  };

}());
(function() {
  window.redirect = function(app){
    var port_name = 'redirect';
    if(!app.ports[port_name]){
      console.warn('Undefined ELM port', port_name);
      return;
    }

    app.ports[port_name].subscribe(function(redirect) {

      // TRASHME
      console.log('Redirect to', redirect.url);
      window.location.href = redirect.url;
      return;

       var redirect_url = url.parse(redirect.url);

       if (redirect.target !== null && redirect.targetName) {
         var query = {};
         query[redirect.targetName] = url.format({
           protocol: window.location.protocol,
           host: window.location.host,
           port: window.location.port,
           pathname: redirect.target[0]
         });
         query['description'] = redirect.target[1];
         redirect_url = url.format(window.$.extend({}, redirect_url, {
          query: query,
         }));
       } else {
         redirect_url = url.format(redirect_url)
       }

     window.location = redirect_url;
    });
  };
}());
var app = Elm.Main.fullscreen();

console.log('Run App', app);
window.localstorage(app, 'bugzilla');
window.localstorage(app, 'taskclusterlogin');
window.redirect(app);
