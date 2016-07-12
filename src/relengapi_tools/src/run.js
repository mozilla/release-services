require('expose?$!expose?jQuery!jquery');
require('expose?Tether!tether');
require('bootstrap');
require("./index.scss");

import app, { sagaMiddleware, sagas } from './index';

app.render()
sagaMiddleware.run(sagas);

window.APP = app;
