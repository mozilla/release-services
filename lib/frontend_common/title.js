'use strict';

module.exports = function(app){

  var port_name = 'set_title';
  if(!app.ports || !app.ports[port_name]){
    console.warn('Undefined ELM port', port_name);  // eslint-disable-line
    return;
  }

  app.ports[port_name].subscribe(function(title){
      document.title = title;
  });

};
