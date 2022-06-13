const proxy = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(proxy('/zoo_models', {target: 'http://0.0.0.0:8000', changeOrigin: true}));
  app.use(proxy('/compile', {target: 'http://0.0.0.0:8000', changeOrigin: true}));
};