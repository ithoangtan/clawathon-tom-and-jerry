import path from "node:path";
import type { ClientRequest, IncomingMessage } from "node:http";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const AGENTBASE_USER_HEADER = "x-greennode-agentbase-user-id";
const GATEWAY_VERIFIED_HEADER = "X-GreenNode-AgentBase-Gateway-Verified";

/** Dev-only: mark proxied SPA identity headers as gateway-trusted for local backend. */
function attachLocalGatewayTrust(
  proxyReq: ClientRequest,
  req: IncomingMessage,
) {
  const hasIdentityHeader = Boolean(
    req.headers[AGENTBASE_USER_HEADER] ??
      proxyReq.getHeader(AGENTBASE_USER_HEADER),
  );
  if (hasIdentityHeader) {
    proxyReq.setHeader(GATEWAY_VERIFIED_HEADER, "true");
  }
}

const apiProxy = {
  target: "http://localhost:8080",
  configure: (proxy: {
    on: (
      event: "proxyReq",
      listener: (proxyReq: ClientRequest, req: IncomingMessage) => void,
    ) => void;
  }) => {
    proxy.on("proxyReq", attachLocalGatewayTrust);
  },
};

// Routes that are BOTH a React client-route (SPA page) AND an API endpoint.
// GET requests must reach the SPA (index.html); only POST/etc go to the backend.
const spaApiProxy = {
  ...apiProxy,
  bypass: (req: IncomingMessage) => {
    if (req.method === "GET") return req.url ?? "/";
  },
};

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/health": apiProxy,
      "/chat": spaApiProxy,
      "/invocations": apiProxy,
      "/feedback": apiProxy,
      "/sync": apiProxy,
      "/api": apiProxy,
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
