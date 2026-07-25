import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
    // Guarantee a single React instance; framer-motion and React Flow both
    // rely on React context across chunk boundaries.
    dedupe: ["react", "react-dom"],
  },
  optimizeDeps: {
    include: ["react", "react-dom", "framer-motion", "@xyflow/react"],
  },
  server: {
    port: 5173,
  },
  build: {
    // Split large, independently-used libraries so a page only downloads
    // what it renders.
    rolldownOptions: {
      output: {
        advancedChunks: {
          groups: [
            { name: "react", test: /node_modules[\\/](react|react-dom|react-router)/ },
            { name: "charts", test: /node_modules[\\/]recharts/ },
            { name: "flow", test: /node_modules[\\/]@xyflow/ },
            {
              name: "markdown",
              test: /node_modules[\\/](react-markdown|remark-|rehype-|highlight\.js|mdast|micromark|hast)/,
            },
          ],
        },
      },
    },
  },
});
