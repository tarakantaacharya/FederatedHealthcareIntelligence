const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Don't proxy requests to /api and /static
  app.use(
    createProxyMiddleware('/api', {
      target: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      changeOrigin: true,
      pathRewrite: {
        '^/api': '/api',
      },
    })
  );
};
