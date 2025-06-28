import App from '@/App.vue'
import '@/assets/main.css'
import '@/check_version'
import router from '@/router'
import * as Sentry from '@sentry/vue'
import Notifications from 'notiwind'
import { createPinia } from 'pinia'
import piniaPluginPersistedState from 'pinia-plugin-persistedstate'
import { createApp } from 'vue'
import { createMetaManager } from 'vue-meta'
import Vue3TouchEvents, { type Vue3TouchEventsOptions } from 'vue3-touch-events'

const app = createApp(App)
if (import.meta.env.VITE_SENTRY_ENABLED) {
  Sentry.init({
    app,
    dsn: 'https://ac53a511c0e049b8b13669b552f3a5c8@o4508993570275328.ingest.de.sentry.io/4508993583644752',
    environment: import.meta.env.PROD ? 'production' : 'development',
    integrations: [
      Sentry.replayIntegration({
        // TODO: change to true for production release
        maskAllText: false,
        blockAllMedia: false
      })
    ],
    // Session Replay
    replaysSessionSampleRate: 1.0, // TODO: change to 0.1 for production release
    replaysOnErrorSampleRate: 1.0
  })
}

const pinia = createPinia()
pinia.use(piniaPluginPersistedState)
app.use(pinia)
app.use(router)
app.use<Vue3TouchEventsOptions>(Vue3TouchEvents, {
  disableClick: false
  // any other global options...
})
app.use(Notifications)
app.use(createMetaManager())
app.mount('#app')
