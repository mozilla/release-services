const fs                = require('fs');
const path              = require( 'path' );
const webpack           = require( 'webpack' );
const merge             = require( 'webpack-merge' );
const HtmlWebpackPlugin = require( 'html-webpack-plugin' );
const ExtractTextPlugin = require( 'extract-text-webpack-plugin' );
const CopyWebpackPlugin = require( 'copy-webpack-plugin' );


// TODO: ssl cert variables should be exposed to nix-shell
// TODO: sourceMap for sass (problem since sass files are in /nix/store)


const CWD = process.cwd();
const TARGET_ENV =
    process.argv[1].indexOf('webpack-dev-server') >= 0 ? 'development' : 'production';
const ENVs = Object
  .keys(process.env)
  .filter(key => key.toUpperCase().startsWith('WEBPACK_'))
  .reduce((env, key) => {
    env[`process.env.${key.substr(8, key.length - 8)}`] = JSON.stringify(process.env[key]);
    return env;
  }, {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV)
  });

const paths = {
  ENTRY         : path.join(CWD, 'src/index.js' ),
  SOURCE        : path.join(CWD, 'src' ),
  OUTPUT        : path.join(CWD, 'build' ),
  NODE_MODULES  : path.join(CWD, 'node_modules')
};

// common webpack config
var commonConfig = {

  // https://webpack.js.org/configuration/output/
  output: {
    path        : paths.OUTPUT,
    filename    : TARGET_ENV === 'production' ? '[name]-[hash].js' : '[name].js',
    publicPath  : '/'
  },

  resolve: {
    modules: [
      paths.SOURCE,
      paths.NODE_MODULES,
      "node_modules"
    ],
    extensions: ['.js', '.elm']
  },

  module: {
    noParse: /\.elm$/,
    rules: [
      {
        test: /\.(eot|ttf|woff|woff2|svg)$/,
        use:  'file-loader'
      }
    ]
  },

  plugins: [
    new webpack.DefinePlugin(ENVs),
    new HtmlWebpackPlugin({
      template: 'src/index.html',
      inject:   'body',
      filename: 'index.html'
    })
  ],

}

// additional webpack settings for local env (when invoked by 'npm start')
if ( TARGET_ENV === 'development' ) {

  module.exports = merge( commonConfig, {

    entry: paths.ENTRY,

    //devtool: "source-map",
    devServer: {
      contentBase: path.SOURCE,

      https: {
        cert: fs.readFileSync(process.env.SSL_CERT),
        key: fs.readFileSync(process.env.SSL_KEY),
        ca: fs.readFileSync(process.env.SSL_CACERT)
      },

      // Enable history API fallback so HTML5 History API based routing works.
      // This is a good default that will come in handy in more complicated
      // setups.
      historyApiFallback: true,

      inline: true,
      hot: true,

      // Display only errors to reduce the amount of output.
      stats: 'errors-only'

    },

    module: {
      rules: [
        {
          test:    /\.elm$/,
          exclude: [/elm-stuff/, /node_modules/],
          use: [
            'elm-hot-loader',
            { loader: 'elm-webpack-loader',
              options: {
                verbose: true,
                warn: true,
                debug: true
              }
            }
          ],
        },
        {
          test: /\.(css|scss)$/,
          use: [
            { loader: 'style-loader',
            },
            {
              loader: 'css-loader',
              //options: {
              //  sourceMap: true,
              //}
            },
            {
              loader: 'sass-loader',
              //options: {
              //  sourceMap: true 
              //}
            }
          ]
        },
        {
          test: /\.(woff|woff2)(\?v=\d+\.\d+\.\d+)?$/,
          loader: 'url-loader',
          query: {
            limit: 10000,
            mimetype: 'application/font-woff'
          }
        },
        {
          test: /\.ttf(\?v=\d+\.\d+\.\d+)?$/,
          loader: 'url-loader',
          options: {
            limit: '10000',
            mimetype: 'application/octet-stream'
          }
        },
        {
          test: /\.eot(\?v=\d+\.\d+\.\d+)?$/,
          loader: 'file-loader'
        },
        {
          test: /\.svg(\?v=\d+\.\d+\.\d+)?$/,
          loader: 'svg-url-loader',
          options: {
            limit: '10000',
            mimetype: 'application/svg+xml'
          }
        },
        {
          test: /\.(png|jpg)$/,
          loader: 'url-loader',
          options: {
            limit: 8192
          }
        },
        {
          test: /\.ico(\?v=\d+\.\d+\.\d+)?$/,
          loader: 'url-loader'
        }



      ]
    },

    plugins: [
      new webpack.HotModuleReplacementPlugin()
    ]
  });
}

// additional webpack settings for prod env (when invoked via 'npm run build')
if ( TARGET_ENV === 'production' ) {

  module.exports = merge( commonConfig, {

    entry: paths.ENTRY,

    module: {
      rules: [
        {
          test:    /\.elm$/,
          exclude: [/elm-stuff/, /node_modules/],
          use:     'elm-webpack-loader'
        },
        {
          test: /\.(css|scss)$/,
          use: ExtractTextPlugin.extract(
            {
              fallback: "style-loader",
              use: [
                {
                  loader: 'css-loader',
                  options: {
                    sourceMap: false,
                    minimize: true,
                    discardComments: {
                      removeAll: true
                    }
                  }
                },
                {
                  loader: 'sass-loader',
                  options: {
                    sourceMap: false
                  }
                }
              ],
              allChunks: true
            })
        }
      ]
    },

    plugins: [
// TODO: copy at least favicon.ico
//      new CopyWebpackPlugin([
//        {
//          from: 'src/static/img/',
//          to:   'static/img/'
//        },
//        {
//          from: 'src/favicon.ico'
//        },
//      ]),

      new webpack.optimize.OccurrenceOrderPlugin(),

      // extract CSS into a separate file
      new ExtractTextPlugin( '[name]-[hash].css' ),

      // minify & mangle JS/CSS
      new webpack.optimize.UglifyJsPlugin({
          compressor: { warnings: false },
          minimize: true,
          output: { comments: false }
          // mangle: true
      })
    ]

  });
}
