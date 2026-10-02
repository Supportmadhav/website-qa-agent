import { defineConfig } from "astro/config";
import react from "@astrojs/react";
export default defineConfig({
  integrations: [react()],
  devToolbar: { enabled: false },
  server: { host: "127.0.0.1", port: 5173 },
  vite: {
    envPrefix: ["PUBLIC_", "VITE_"],
    optimizeDeps: { include: ["jspdf", "jspdf-autotable"] },
    server: { strictPort: true },
  },
});
