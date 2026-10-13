import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  build: { rollupOptions: { output: { manualChunks: { charts: ["echarts/core", "echarts/charts", "echarts/components", "echarts/renderers"] } } } },
  plugins: [react()],
  server: {
    port: 5173,
  },
});
