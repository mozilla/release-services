
const isObject = (data) => {
  return typeof data === typeof {};
};

const parse = (data) => {
  let out = null;
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

export default (app, key) => {

  app.ports.localstorage_load.subscribe((key) => {
    app.ports.localstorage_get.send(key, parse(window.localStorage.getItem(key)));
  });

  app.ports.localstorage_remove.subscribe((key) => {
    window.localStorage.removeItem(key);
    app.ports.localstorage_get.send(key, null);
  });

  app.ports.localstorage_set.subscribe((key, new_data) => {
    let data = parse(window.localStorage.getItem(key));

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
    app.ports.localstorage_get.send(key, data);
  });

};
