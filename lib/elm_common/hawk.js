var Hawk = require('hawk');

module.exports = function(app){

  var port_name = 'hawk_add_header';
  if(!app.ports || !app.ports[port_name]){
    console.warn('Undefined ELM port', port_name);
    return;
  }

  app.ports[port_name].subscribe(function(settings, request, user){
    console.debug('In hawk_add_header');

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

    // Send back headers
    app.ports.hawk_send_request.send(settings, request);
  });
};
