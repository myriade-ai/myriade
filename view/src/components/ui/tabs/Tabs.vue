<template>
  <div class="tabs-root">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { provide, ref, onMounted } from 'vue'
import type { Ref } from 'vue'

interface Props {
  defaultValue?: string
}

const props = withDefaults(defineProps<Props>(), {
  defaultValue: 'overview'
})

const activeTab: Ref<string> = ref(props.defaultValue || 'overview')

provide('activeTab', activeTab)

function setActiveTab(value: string) {
  activeTab.value = value
}

provide('setActiveTab', setActiveTab)

// Initialize on mount to ensure proper setup
onMounted(() => {
  if (!activeTab.value) {
    activeTab.value = props.defaultValue || 'overview'
  }
})
</script>
