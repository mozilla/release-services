'use strict';

const webpackConfig = require('neo/webpack');

module.exports = webpackConfig(
  __dirname,
  // index.html config
  { title: 'RelengAPI Tools'
  , description: 'Collection of Mozilla Release Engineering Tools'
  , author: 'Mozilla RelEng Team'
  , head: '<link href="https://fonts.googleapis.com/css?family=Fira+Sans:400,300,500" rel="stylesheet" type="text/css">'
  },
  // .. custom webpack configuration
  {}

);
