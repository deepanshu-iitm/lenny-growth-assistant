import { defineConfig } from "vite";

export default defineConfig({
  esbuild: { jsx: "automatic" },
  server: {
    port: 5173,
    proxy: {
      "/sessions": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/ready": "http://127.0.0.1:8000",
      "/admin": "http://127.0.0.1:8000",
    },
  },
});
