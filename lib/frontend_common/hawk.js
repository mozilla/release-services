'use strict';

var Hawk = require('hawk/client.js');

module.exports = function(app){

  var port_name = 'hawk_add_header';
  if(!app.ports || !app.ports[port_name]){
    console.warn('Undefined ELM port', port_name);  // eslint-disable-line
    return;
  }

  app.ports[port_name].subscribe(function(parameters){
    var request = JSON.parse(parameters[0])
    var credentials = parameters[1];

    // Transform body to ease elm parsing
    if(request.body !== null && request.body.startsWith('StringBody ')){
      var body = request.body.substr(11);
      // Parse json
      if(body.startsWith('"application/json" ')){
        body = body.substr(18);
        try {
          request.body = JSON.parse(body);
        }catch(e){
          request.body = body;
        }
      }else{
        request.body = body;
      }
    }

    // Parse existing headers as Elm gives a string representation
    var headerRegex = /^Header "(.+)" "(.+)"$/;
    var headers = [];
    for(var i in request.headers){
      var match = headerRegex.exec(request.headers[i]);
      if(match === null)
        continue;
      headers.push([match[1], match[2]]);
    }
    request.headers = headers;

    // Build optional cert
    var extData = null;
    if(credentials.certificate)
      extData = new Buffer(JSON.stringify({certificate: JSON.parse(credentials.certificate)})).toString('base64');

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
    request.headers.push(['Authorization', header.field]);

    // Send back headers
    app.ports.hawk_send_request.send(JSON.stringify(request));
  });
};
