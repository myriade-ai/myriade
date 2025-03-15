import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './assets/main.css'
import App from './App.vue'
import { createMetaManager } from 'vue-meta'
import LayoutDefault from '@/layouts/default.vue'

import piniaPluginPersistedState from 'pinia-plugin-persistedstate'
import router from './router'
import Vue3TouchEvents, { type Vue3TouchEventsOptions } from 'vue3-touch-events'

const app = createApp(App)
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
