const Path = require('path');
const Webpack = require('webpack');
const { merge } = require('webpack-merge');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const ESLintPlugin = require('eslint-webpack-plugin');

const common = require('./webpack.config.js');

module.exports = merge(common, {
  target: 'web',
  mode: 'development',
  devtool: 'source-map',
  output: {
    chunkFilename: 'js/[name].chunk.js',
    filename: 'js/[name].js',
    publicPath: 'http://localhost:9091/',
  },
  devServer: {
    hot: true,
    port: 9091,
    headers: {
      "Access-Control-Allow-Origin": "*",
    }, 
    devMiddleware: {
      writeToDisk: true,
    }
  },
  plugins: [
    new Webpack.DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify('development'),
    }),
    new MiniCssExtractPlugin({ filename: 'css/[name].css', }),
    new ESLintPlugin({
      fix: true,
    }),
  ],
  module: {
    rules: [
      {
        test: /\.html$/i,
        loader: 'html-loader',
      },
      
    ],
  }
});
