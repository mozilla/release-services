let config = require(
    'mozilla-neo/config/webpack.' +
     (process.env.npm_lifecycle_event === 'build' ? 'prod' : 'dev'));

const ELM_EXT = /\.elm$/;

config.module.loaders.push({
  test: ELM_EXT,
  exclude: /(node_modules|elm-stuff)/,
  loader: 'elm-webpack'
});

config.module.noParse = ELM_EXT;

module.exports = config;
