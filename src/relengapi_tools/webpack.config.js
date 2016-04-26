const HtmlWebpackPlugin = require('html-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const merge = require('webpack-merge');
const path = require('path');
const webpack = require('webpack');

// Detect how npm is run and branch based on that
const __DEV__ = process.env.npm_lifecycle_event === "dev";
const __PROD__ = process.env.npm_lifecycle_event === 'build';

const PATHS = {
  app: path.join(__dirname, 'src'),
  build: path.join(__dirname, 'build')
};


const common = {
    entry: {
      app: PATHS.app
    },
    output: {
      path: PATHS.build,
      filename: '[name].js'  // Output using the entry name
    },
    plugins: [
      new HtmlWebpackPlugin({
        templateContent: '' +
          '<!doctype html>\n' +
          '<html>\n' +
          '  <head>\n' +
          '    <meta charset="utf-8">\n' +
          '    <meta http-equiv="X-UA-Compatible" content="IE=edge">\n' +
          '    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">\n' +
          '    <meta name="description" content="Collection of Mozilla Release Engineering Tools">\n' +
          '    <meta name="author" content="Mozilla RelEng Team">\n' +
          '    <title>RelengAPI Tools</title>\n' +
          '    <link href="https://fonts.googleapis.com/css?family=Fira+Sans:400,300,500" rel="stylesheet" type="text/css">\n' +
          '  </head>\n' +
          '  <body>\n' +
          '    <div id="app"></div>\n' +
          '  </body>\n' +
          '</html>'
      }),
      new webpack.DefinePlugin({
        '__DEV__': __DEV__.toString(),
        'process.env.NODE_ENV': __PROD__ ? '"production"' : '""'  // needed to build redux for production
      })
    ],
    module: {
      loaders: [
        { loaders: [ 'babel?presets[]=es2015&presets[]=stage-0&presets[]=react' ,'eslint' ],
          test: /\.jsx?$/,
          exclude: /(node_modules|bower_components|build)/
        }
      ]
    },
    resolve: {
      extenstions: ['', '.js']
    }
}


if (__DEV__) {
  module.exports = merge(common, {
    devtool: 'source-map',
    devServer: {
      // Enable history API fallback so HTML5 History API based
      // routing works. This is a good default that will come
      // in handy in more complicated setups.
      historyApiFallback: true,
      hot: true,
      inline: true,
      progress: true,

      // Display only errors to reduce the amount of output.
      stats: 'errors-only',

      // Parse host and port from env to allow customization.
      //
      // If you use Vagrant or Cloud9, set
      // host: process.env.HOST || '0.0.0.0';
      //
      // 0.0.0.0 is available to all network devices
      // unlike default localhost
      host: process.env.HOST,
      port: process.env.PORT

      // If you want defaults, you can use a little trick like this
      // port: process.env.PORT || 3000
    },
    plugins: [
      new webpack.HotModuleReplacementPlugin(),
      new webpack.NoErrorsPlugin(), // because of https://github.com/MoOx/eslint-loader#noerrorsplugin
      new webpack.DefinePlugin({ __DEV__: 'true' })
    ],
  });


} else if(__PROD__) {

  module.exports = merge(common, {
    plugins: [
      new CleanWebpackPlugin([PATHS.build]),
      new webpack.optimize.UglifyJsPlugin({
        compress: {
          warnings: false
        }
      })
    ]
  });

} else {
  module.exports = common;
}

