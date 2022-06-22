const path = require('path');

module.exports = {
  entry: './sparrow/static/scripts/app.js',  // path to our input file
  output: {
    filename: 'app.bundle.js',  // output bundle file name
    path: path.resolve(__dirname, './sparrow/static/scripts'),
  },
};