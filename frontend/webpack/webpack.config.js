const Path = require('path');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const { VueLoaderPlugin } = require('vue-loader')
const BundleTracker = require('webpack-bundle-tracker'); 

module.exports = {
  entry: {
    app: Path.resolve(__dirname, '../src/scripts/index'),
    vue: Path.resolve(__dirname, '../src/scripts/vue'),
    typewriter: Path.resolve(__dirname, '../src/scripts/plugins/typewriter'),
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
      'vue': 'vue/dist/vue.esm.js',
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
        test: /\.(ico|jpg|jpeg|png|gif|webp|svg)(\?.*)?$/,
        use: {
          loader: 'file-loader',
          options: {
            name: '[path][name].[ext]',
          },
        },
      },
    ],
  },
};
