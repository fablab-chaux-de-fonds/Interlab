const Path = require('path');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const autoprefixer = require('autoprefixer')
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const { VueLoaderPlugin } = require('vue-loader')
const BundleTracker = require('webpack-bundle-tracker'); 
const webpack = require("webpack");

module.exports = {
  entry: {
    index: Path.resolve(__dirname, '../src/js/index'),
    app: Path.resolve(__dirname, '../src/js/app'),
    vue: Path.resolve(__dirname, '../src/js/vue'),
  },
  output: {
    path: Path.join(__dirname,'..','..', 'build'),
    filename: '[name].js',
    publicPath: '/static/',
  },
  optimization: {
    splitChunks: {
      chunks: 'all',
      name: 'vendors', 
    },
  },
  plugins: [
    new CleanWebpackPlugin(),
    new BundleTracker({ path: Path.join(__dirname,'..','..', 'build'), filename: "webpack-stats.json" }),
    new VueLoaderPlugin(),
  ],
  resolve: {
    alias: {
      '~': Path.resolve(__dirname, '../src'),
    },
    extensions: [".js", ".vue", ".json"],
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        include: Path.resolve(__dirname, '../src'),
        loader: 'babel-loader',
      },
      {
        test: /\.css$/,
        use: [ 
          MiniCssExtractPlugin.loader,
          'css-loader'
        ]
      },
      {
        test: /\.vue$/,
        loader: 'vue-loader'
      },
      {
        test: /\.s(c|a)ss$/,
        use: [
          MiniCssExtractPlugin.loader,
          'css-loader',
          {
            loader: 'sass-loader',
            options: {
              implementation: require('sass'),
            },
          },
        ],
      },
      {
        test: /\.mjs$/,
        include: /node_modules/,
        type: 'javascript/auto',
      },
      {
        test: /\.(ico|jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2)(\?.*)?$/,
        use: {
          loader: 'file-loader',
          options: {
            name: '[path][name].[ext]',
          },
        },
      },
      {
        test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        include: Path.resolve(__dirname, './node_modules/bootstrap-icons/font/fonts'),
        use: {
          loader: 'file-loader',
          options: {
            name: '[path][name].[ext]',
          },
        }
      }
    ],
  },
};
