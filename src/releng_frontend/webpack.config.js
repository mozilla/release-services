const fs = require('fs');
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
  config.devServer.cacert = fs.readFileSync(process.env.SSL_CACERT);
  config.devServer.cert = fs.readFileSync(process.env.SSL_CERT);
  config.devServer.key= fs.readFileSync(process.env.SSL_KEY);
}

module.exports = config;
