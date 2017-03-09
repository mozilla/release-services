'use strict';

var Hawk = require('hawk/client.js');

module.exports = function(app){

  var port_name = 'hawk_add_header';
  if(!app.ports || !app.ports[port_name]){
    console.warn('Undefined ELM port', port_name);  // eslint-disable-line
    return;
  }

  app.ports[port_name].subscribe(function(parameters){
    var requestId = parameters[0];
    var request = JSON.parse(parameters[1])
    var credentials = parameters[2];

    // Transform body to ease elm parsing
    if(request.body == 'Empty'){
      request.body = null;
    }else if(request.body.startsWith('BodyString ')){
      var body = request.body.substr(11);
      try {
        request.body = JSON.parse(body);
      }catch(e){
        request.body = body;
      }
    }

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
    var header = Hawk.client.header(request.url, request.method, payload);
    request['headers'].push(['Authorization', header.field]);

    // Send back headers
    app.ports.hawk_send_request.send(JSON.stringify([requestId, request]));
  });
};
