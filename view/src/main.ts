import LayoutDefault from '@/layouts/default.vue'
import * as Sentry from '@sentry/vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedState from 'pinia-plugin-persistedstate'
import { createApp } from 'vue'
import { createMetaManager } from 'vue-meta'
import Vue3TouchEvents, { type Vue3TouchEventsOptions } from 'vue3-touch-events'
import App from './App.vue'
import './assets/main.css'
import './check_version'
import router from './router'

const app = createApp(App)
Sentry.init({
  app,
  dsn: 'https://ac53a511c0e049b8b13669b552f3a5c8@o4508993570275328.ingest.de.sentry.io/4508993583644752',
  environment: import.meta.env.PROD ? 'production' : 'development'
})

const pinia = createPinia()
pinia.use(piniaPluginPersistedState)
app.use(pinia)
app.use(router)

app.use<Vue3TouchEventsOptions>(Vue3TouchEvents, {
  disableClick: false
  // any other global options...
})

app.component('layout-default', LayoutDefault)
app.use(createMetaManager())
app.mount('#app')
