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
  title: 'Ada',
  description: 'Explore your data with Ada!',
  htmlAttrs: { lang: 'en' }
})

const layout = computed<string>(() => {
  return `layout-${useRoute().meta.layout || 'default'}`
})
</script>
