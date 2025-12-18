// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

/* Modified to use Azure Function Proxy for public access
   No authentication required - the Azure Function handles auth via Managed Identity */

const { createProxyMiddleware } = require("http-proxy-middleware");

// Azure Function Proxy endpoint
const AZURE_FUNCTION_PROXY = "https://adt-telemetry-router.azurewebsites.net";

module.exports = function (app) {
  // Simple proxy that forwards all requests to the Azure Function Proxy
  // The Azure Function handles authentication and communicates with Azure Digital Twins
  
  app.use(
    "/api/proxy",
    createProxyMiddleware({
      target: AZURE_FUNCTION_PROXY,
      changeOrigin: true,
      pathRewrite: (path, req) => {
        // Remove /api/proxy prefix and forward to /api/dt
        const newPath = path.replace("/api/proxy", "/api/dt");
        console.log(`Proxying: ${path} -> ${newPath}`);
        return newPath;
      },
      onProxyReq: (proxyReq, req, res) => {
        // Remove origin headers that might cause CORS issues
        if (proxyReq.getHeader("origin")) {
          proxyReq.removeHeader("origin");
          proxyReq.removeHeader("referer");
        }
        
        // Extract ADT host from x-adt-host header (set by CustomHttpClient in ApiService.js)
        const adtHost = req.headers["x-adt-host"];
        if (adtHost) {
          console.log(`Request for ADT host: ${adtHost}`);
        }
      },
      onError: (err, req, res) => {
        console.error("Proxy error:", err);
        res.status(500).json({ error: "Proxy error", message: err.message });
      }
    })
  );
};
