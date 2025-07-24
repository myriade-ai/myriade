import { sentryVitePlugin } from '@sentry/vite-plugin'
import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vitejs.dev/config/
export default defineConfig({
  // build: {
  //   commonjsOptions: {
  //     esmExternals: true
  //   }
  // },
  plugins: [
    vue(),
    sentryVitePlugin({
      org: 'myriade-ai',
      project: 'view',
      authToken: process.env.SENTRY_AUTH_TOKEN
    })
  ],

  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8080'
      },
      '/socket.io': {
        target: 'http://127.0.0.1:8080',
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
