const fs = require('fs');
const config = require('mozilla-neo/config/webpack.dev');
const ELM_EXT = /\.elm$/;

// Remove react-hot from config
config.module.loaders = config.module.loaders.filter(function(loader){
  return !(loader['loaders'] && loader['loaders'].indexOf('react-hot') > -1);
});

config.module.loaders.push({
  test: ELM_EXT,
  exclude: /(node_modules|elm-stuff)/,
  loader: 'elm-webpack'
});

config.module.noParse = ELM_EXT;

module.exports = config;
