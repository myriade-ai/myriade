<template>
  <div
    v-show="isActive"
    :class="[
      'ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-950 focus-visible:ring-offset-2',
      $attrs.class
    ]"
    :data-state="isActive ? 'active' : 'inactive'"
    tabindex="0"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { inject, computed } from 'vue'
import type { Ref } from 'vue'

interface Props {
  value: string
}

const props = defineProps<Props>()

const activeTab = inject<Ref<string>>('activeTab')

const isActive = computed(() => activeTab?.value === props.value)
</script>
