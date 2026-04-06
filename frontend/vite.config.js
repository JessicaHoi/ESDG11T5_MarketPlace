import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://kong:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/sse': {
        target: 'http://notification-service:5002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/sse/, ''),
        // Required for SSE: disable response buffering
        configure: (proxy) => {
          proxy.on('proxyRes', (proxyRes) => {
            proxyRes.headers['cache-control'] = 'no-cache'
            proxyRes.headers['x-accel-buffering'] = 'no'
          })
        }
      }
    }
  }
})
