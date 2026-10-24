var _a, _b;
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        host: '0.0.0.0',
        proxy: {
            '/api': (_a = process.env.API_PROXY_TARGET) !== null && _a !== void 0 ? _a : 'http://localhost:8000',
            '/auth': (_b = process.env.API_PROXY_TARGET) !== null && _b !== void 0 ? _b : 'http://localhost:8000',
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
