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

module.exports = function(app, namespace) {

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

  console.info('Initialized localstorage for', namespace);
};
