<template>
  <div class="flex items-center">
    <BaseSelector
      :options="contextsStore.contexts"
      v-model="contextsStore.contextSelected"
      @update:modelValue="contextsStore.setSelectedContext"
      class="w-48"
      placeholder="Select context"
      :disabled="disabled"
    />
  </div>
</template>

<script setup lang="ts">
import BaseSelector from '@/components/base/BaseSelector.vue'
import { useContextsStore } from '@/stores/contexts'
import { onMounted } from 'vue'

defineProps<{
  disabled?: boolean
}>()

const contextsStore = useContextsStore()

onMounted(() => {
  contextsStore.initializeContexts()
})
</script>
