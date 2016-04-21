var glob = require("glob")
var merge = require('webpack-merge');
var webpackConfig = require('./webpack.config');

var files = glob.sync("tests/*-test.js")
var preprocessors = files.reduce(function(i, j) { i[j] = [ 'webpack', 'sourcemap' ]; return i; }, {});

module.exports = function (config) {
  config.set({
    browsers: [ 'Chrome' ],
    singleRun: true,
    frameworks: [ 'mocha' ],
    plugins: [
      'karma-chai',
      'karma-chrome-launcher',
      'karma-coverage',
      'karma-mocha',
      'karma-mocha-reporter',
      'karma-sourcemap-loader',
      'karma-webpack'
    ],
    files: files,
    preprocessors: preprocessors,
    reporters: [ 'mocha', 'coverage' ],
    webpack: merge(webpackConfig, {
      // https://github.com/airbnb/enzyme/issues/47#issuecomment-207498885
      externals: {
        'react/lib/ExecutionEnvironment': true,
        'react/lib/ReactContext': true,
        'react/addons': true
      },
      devtool: 'inline-source-map',
      module: {
        // https://github.com/airbnb/enzyme/issues/47#issuecomment-171953666
        loaders: [
          { test: /\.json$/,
            loader: "json" 
          }
        ],
        postLoaders: [
          { test: /\.js$/,
            exclude: /(tests|node_modules)\//,
            loader: 'istanbul-instrumenter'
          }
        ]
      }
    }),
    webpackServer: {
      noInfo: true //please don't spam the console when running in karma!
    },
    coverageReporter: {
      dir: 'coverage/',
      reporters: [
        { type: 'html', subdir: 'report-html' },
        { type: 'lcov', subdir: 'report-lcov' },
        { type: 'cobertura', subdir: '.', file: 'cobertura.txt' }
      ]
    }
  });
};
