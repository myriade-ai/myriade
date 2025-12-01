import { sentryVitePlugin } from '@sentry/vite-plugin'
import path from 'node:path'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vitejs.dev/config/
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          echarts: ['echarts', 'vue-echarts'],
          tiptap: [
            '@tiptap/core',
            '@tiptap/vue-3',
            '@tiptap/starter-kit',
            '@tiptap/extension-bubble-menu',
            '@tiptap/extension-mention',
            '@tiptap/extension-placeholder',
            '@tiptap/suggestion',
            'tiptap-markdown'
          ]
        }
      }
    }
  },
  plugins: [
    vue(),
    process.env.SENTRY_AUTH_TOKEN &&
      sentryVitePlugin({
        org: 'myriade-ai',
        project: 'view',
        authToken: process.env.SENTRY_AUTH_TOKEN
      })
  ].filter(Boolean),

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
      '@': path.resolve(__dirname, './src')
    }
  }
})
