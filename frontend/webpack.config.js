const path = require("path");
var webpack = require("webpack");
const HtmlWebpackPlugin = require("html-webpack-plugin");
require("dotenv").config(); // ⬅️ Loads .env variables into process.env
module.exports = {
  entry: "./src/index.tsx",
  devtool: "source-map", // or 'eval-source-map' for development
  output: {
    path: path.resolve(__dirname, "build"),
    filename: "bundle.js",
    clean: true,
    publicPath: "/",
  },
  resolve: {
    extensions: [".ts", ".tsx", ".js", ".jsx"],
  },
  module: {
    rules: [
      {
        test: /\.(ts|tsx|js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
          options: {
            presets: [
              "@babel/preset-env",
              "@babel/preset-react",
              "@babel/preset-typescript",
            ],
          },
        },
      },
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"],
      },
      {
        test: /\.(png|jpe?g|gif|svg)$/i,
        type: "asset/resource", // built-in asset module
      },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: "./public/index.html",
    }),
    new webpack.DefinePlugin({
      // Define process.env.REACT_APP_* variables individually
      // This allows process.env.REACT_APP_* to work in the browser
      ...Object.keys(process.env)
        .filter((key) => key.startsWith("REACT_APP_"))
        .reduce((defines, key) => {
          defines[`process.env.${key}`] = JSON.stringify(process.env[key]);
          return defines;
        }, {}),
      // Define process.env as an empty object fallback to prevent "process is not defined" errors
      "process.env": JSON.stringify(
        Object.keys(process.env)
          .filter((key) => key.startsWith("REACT_APP_"))
          .reduce((env, key) => {
            env[key] = process.env[key];
            return env;
          }, {})
      ),
    }),
  ],
  devServer: {
    static: {
      directory: path.resolve(__dirname, "public"),
    },
    port: 8080,
    historyApiFallback: true, // if you're using routing
    open: true,
  },
  mode: "development",
  ignoreWarnings: [
    {
      module: /node_modules/,
      message: /Failed to parse source map/,
    },
  ],
};
