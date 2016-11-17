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
