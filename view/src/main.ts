import LayoutDefault from '@/layouts/default.vue'
import { createPinia } from 'pinia'
import { createApp } from 'vue'
import { createMetaManager } from 'vue-meta'
import App from './App.vue'
import './assets/main.css'

import * as Sentry from '@sentry/vue'
import piniaPluginPersistedState from 'pinia-plugin-persistedstate'
import Vue3TouchEvents, { type Vue3TouchEventsOptions } from 'vue3-touch-events'
import router from './router'

const app = createApp(App)
Sentry.init({
  app,
  dsn: 'https://ac53a511c0e049b8b13669b552f3a5c8@o4508993570275328.ingest.de.sentry.io/4508993583644752'
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
