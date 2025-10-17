<template>
  <button
    type="button"
    class="flex w-full flex-col gap-1 rounded-lg px-2 py-2 text-left text-sm transition-all duration-200"
    :class="[
      isSelected
        ? 'bg-gradient-to-r from-blue-50 to-slate-100 text-primary-900 ring-1 ring-primary-400 shadow-sm'
        : 'text-muted-foreground hover:bg-gradient-to-r hover:from-slate-100 hover:to-stone-100'
    ]"
    @click="emit('select')"
  >
    <div class="flex items-center justify-between gap-2">
      <div class="flex items-center gap-2 truncate">
        <component :is="iconComponent" class="h-4 w-4 flex-shrink-0 text-primary-600" />
        <span class="truncate text-foreground">{{ label }}</span>
      </div>
      <span v-if="meta" class="text-xs text-muted-foreground">{{ meta }}</span>
    </div>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Columns3, Table as TableIcon } from 'lucide-vue-next'

const props = defineProps<{
  label: string
  type: 'table' | 'column'
  isSelected?: boolean
  meta?: string
}>()

const emit = defineEmits<{
  (e: 'select'): void
}>()

const iconComponent = computed(() => (props.type === 'table' ? TableIcon : Columns3))
</script>
