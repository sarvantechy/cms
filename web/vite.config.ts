import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const environment = loadEnv(mode, ".", "VITE_");
  const proxyTarget = environment.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    server: {
      host: "127.0.0.1",
      proxy: {
        "/api": proxyTarget,
        "/health": proxyTarget,
      },
    },
  };
});
