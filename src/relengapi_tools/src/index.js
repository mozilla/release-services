'use strict';

require('expose?$!expose?jQuery!jquery');
require('expose?Tether!tether');
require('bootstrap');
require("./index.scss");
require('./Main.elm').Main.embed(document.getElementById('root'));
