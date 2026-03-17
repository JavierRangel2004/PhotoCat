import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [svelte()],
  server: {
    port: Number(process.env.PHOTOCAT_DESKTOP_PORT ?? "4173"),
  },
});
