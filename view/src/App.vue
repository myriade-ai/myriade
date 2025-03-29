<template>
  <metainfo>
    <template v-slot:title="{ content }">{{ content }}</template>
  </metainfo>
  <component :is="layout"> </component>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { useMeta } from 'vue-meta'
import { useRoute } from 'vue-router'

useMeta({
  title: 'Myriade',
  description: 'Explore your data with Myriade!',
  htmlAttrs: { lang: 'en' }
})

const route = useRoute()

const layout = computed<string>(() => {
  return `layout-${route?.meta?.layout || 'default'}`
})
</script>
