import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  envDir: '..',
  plugins: [vue()],
  server: {
    port: 5173,
    strictPort: true,
    watch: { usePolling: process.env.CHOKIDAR_USEPOLLING === 'true' },
    allowedHosts: true,
  },
})
