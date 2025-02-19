import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  // build: {
  //   commonjsOptions: {
  //     esmExternals: true
  //   }
  // },
  plugins: [vue()],
  server: {
    proxy: {
      '/auth': {
        target: 'http://127.0.0.1:4000',
        rewrite: (path) => path.replace(/^\/auth/, '')
      },
      '/api': {
        target: 'http://127.0.0.1:4000',
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/socket.io': {
        target: 'http://127.0.0.1:4000',
        changeOrigin: true,
        ws: true
      }
    }
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})
