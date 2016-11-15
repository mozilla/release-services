
(function() {

  var url = require('url');

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
  
  window.app_user = function(app, key) {
  
    if (!app.ports) {
      return
    }
  
    app.ports.user_load.subscribe(function() {
      app.ports.user_get.send(parse(window.localStorage.getItem(key)));
    });
  
    app.ports.user_remove.subscribe(function() {
      window.localStorage.removeItem(key);
      app.ports.user_get.send(null);
    });
  
    app.ports.user_set.subscribe(function(new_data) {
      var data = parse(window.localStorage.getItem(key));
  
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
  
      window.localStorage.setItem(key, JSON.stringify(data));
      app.ports.user_get.send(data);
    });
  
    app.ports.redirect.subscribe(function(redirect) {
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
