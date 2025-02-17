import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './assets/main.css'
import App from './App.vue'
import { createMetaManager } from 'vue-meta'
import LayoutDefault from '@/layouts/default.vue'
import VueFusionCharts from 'vue-fusioncharts'

// import FusionCharts modules and resolve dependency
import FusionCharts from 'fusioncharts'
import Charts from 'fusioncharts/fusioncharts.charts'
import FusionTheme from 'fusioncharts/themes/fusioncharts.theme.fusion'
import piniaPluginPersistedState from 'pinia-plugin-persistedstate'
import router from './router'
import Vue3TouchEvents, { type Vue3TouchEventsOptions } from 'vue3-touch-events'
import { clerkPlugin } from '@clerk/vue'

const PUBLISHABLE_KEY = "pk_test_ZXBpYy10aWdlci00Ny5jbGVyay5hY2NvdW50cy5kZXYk"

if (!PUBLISHABLE_KEY) {
  throw new Error('Add your Clerk Publishable Key to the .env.local file')
}

const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPluginPersistedState)
app.use(pinia)
app.use(router)

app.use<Vue3TouchEventsOptions>(Vue3TouchEvents, {
  disableClick: false
  // any other global options...
})

// eslint-disable-next-line vue/component-definition-name-casing
app.component('layout-default', LayoutDefault)
app.use(createMetaManager())
app.use(VueFusionCharts, FusionCharts, Charts, FusionTheme)
app.use(clerkPlugin, { publishableKey: PUBLISHABLE_KEY })
app.mount('#app')