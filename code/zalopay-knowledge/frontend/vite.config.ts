import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

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
      "/health": "http://localhost:8080",
      "/chat": "http://localhost:8080",
      "/invocations": "http://localhost:8080",
      "/feedback": "http://localhost:8080",
      "/sync": "http://localhost:8080",
      "/api/dashboard": "http://localhost:8080",
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
