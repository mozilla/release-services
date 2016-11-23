var Hawk = require('hawk/client.js');

module.exports = function(app){

  var port_name = 'hawk_add_header';
  if(!app.ports || !app.ports[port_name]){
    console.warn('Undefined ELM port', port_name);
    return;
  }

  app.ports[port_name].subscribe(function(parameters){
    var requestId = parameters[0];
    var request = JSON.parse(parameters[1])
    var credentials = parameters[2];

    // Build optional cert
    var extData = null;
    if(credentials.certificate)
      extData = new Buffer(JSON.stringify({certificate: credentials.certificate})).toString('base64');

    // Generic payload for both headers
    var payload = {
      credentials: {
        id: credentials.clientId,
        key: credentials.accessToken,
        algorithm: 'sha256'
      },
      ext: extData,
    };

    // Build HAWK header & store it in request
    var header = Hawk.client.header(request.url, request.verb, payload);
    request['headers'].push(['Authorization', header.field]);

    // Send back headers
    app.ports.hawk_send_request.send(JSON.stringify([requestId, request]));
  });

  console.info('Initialized hawk');
};
