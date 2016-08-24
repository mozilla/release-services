const config_type = process.argv.indexOf('start') !== -1 ? 'dev' : 'prod';
const config = require('mozilla-neo/config/webpack.' + config_type);
const ELM_EXT = /\.elm$/;

config.module.loaders.push({
  test: ELM_EXT,
  exclude: /(node_modules|elm-stuff)/,
  loader: 'elm-webpack'
});

config.module.noParse = ELM_EXT;

if (config_type === 'dev') {
  config.devServer.https = true;
}

module.exports = config;
