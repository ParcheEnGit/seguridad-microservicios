import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    // En Docker sobre Windows los cambios del volumen no generan eventos; se revisan por sondeo.
    watch: { usePolling: true, interval: 300 },
    proxy: {
      "/api": {
        target: process.env.VITE_PROXY_API_TARGET || "http://localhost:8080",
        changeOrigin: true,
      },
    },
  },
});
