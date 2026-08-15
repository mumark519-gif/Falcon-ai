import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The React plugin was already listed in package.json but never wired up
// anywhere, so JSX/TSX was previously relying on esbuild's bare-bones
// transform with no Fast Refresh. This wires it up properly and adds a
// dev-server proxy to the backend so VITE_API_URL can just be "/api" in
// development without fighting CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_BACKEND_URL || "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
