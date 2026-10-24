import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': process.env.API_PROXY_TARGET ?? 'http://localhost:8000',
      '/auth': process.env.API_PROXY_TARGET ?? 'http://localhost:8000',
    },
  },
  preview: {
    port: 4173,
    host: '0.0.0.0',
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
});
