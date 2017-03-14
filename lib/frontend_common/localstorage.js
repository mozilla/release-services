'use strict';

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

var load_item = function(namespace){
  return parse(window.localStorage.getItem(namespace));
};

module.exports = {
  load_item : load_item,
  init : function(app, namespace) {

    var port_name_load = namespace + '_load';
    if(!app.ports || !app.ports[port_name_load]){
      console.warn('Undefined ELM port', port_name_load);  // eslint-disable-line
      return;
    }

    var port_name_remove = namespace + '_remove';
    if(!app.ports || !app.ports[port_name_remove]){
      console.warn('Undefined ELM port', port_name_remove);  // eslint-disable-line
      return;
    }

    var port_name_set = namespace + '_set';
    if(!app.ports || !app.ports[port_name_set]){
      console.warn('Undefined ELM port', port_name_set);  // eslint-disable-line
      return;
    }

    var port_name_get = namespace + '_get';
    if(!app.ports || !app.ports[port_name_get]){
      console.warn('Undefined ELM port', port_name_get);  // eslint-disable-line
      return;
    }

    app.ports[port_name_load].subscribe(function() {
      app.ports[port_name_get].send(load_item(namespace));
    });

    app.ports[port_name_remove].subscribe(function() {
      window.localStorage.removeItem(namespace);
      app.ports[port_name_get].send(null);
    });

    app.ports[port_name_set].subscribe(function(new_data) {
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
      app.ports[port_name_get].send(data);
    });
  },
};
