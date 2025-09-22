<template>
  <button
    @click="setActiveTab?.(value)"
    :class="[
      'inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-950 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
      isActive ? 'bg-white text-gray-950 shadow-sm' : 'hover:bg-gray-200/80 hover:text-gray-900'
    ]"
    :data-state="isActive ? 'active' : 'inactive'"
    type="button"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
import { inject, computed } from 'vue'
import type { Ref } from 'vue'

interface Props {
  value: string
}

const props = defineProps<Props>()

const activeTab = inject<Ref<string>>('activeTab')
const setActiveTab = inject<(value: string) => void>('setActiveTab')

const isActive = computed(() => activeTab?.value === props.value)
</script>
