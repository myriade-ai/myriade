<template>
  <div v-if="appReady">
    <metainfo>
      <template v-slot:title="{ content }">{{ content }}</template>
    </metainfo>
    <component :is="layout"> </component>
  </div>
  <div v-else class="initial-loading" />
</template>

<script lang="ts" setup>
import { computed, defineAsyncComponent, onMounted, ref } from 'vue'
import { useMeta } from 'vue-meta'
import { useRoute } from 'vue-router'

useMeta({
  title: 'Myriade',
  description: 'Explore your data with Myriade!',
  htmlAttrs: { lang: 'en' }
})

const route = useRoute()
const appReady = ref(false)

onMounted(() => {
  // This ensures the app shows nothing until it's fully ready
  requestAnimationFrame(() => {
    appReady.value = true
  })
})

const layout = computed<string>(() => {
  if (route.name === undefined) {
    return '' // Empty so we don't have flickering
  }
  const layoutName = route.meta.layout || 'default'
  return defineAsyncComponent(() => import(`./layouts/${layoutName}.vue`))
})
</script>
