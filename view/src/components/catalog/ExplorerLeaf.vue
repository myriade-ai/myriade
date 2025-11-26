<template>
  <div
    class="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-sm transition-all duration-200"
    :class="[
      selectionMode ? '' : 'cursor-pointer',
      isSelected
        ? 'bg-gradient-to-r from-primary-50 to-muted dark:from-primary-900/30 dark:to-muted/30 text-primary-900 dark:text-primary-100 ring-1 ring-primary-400 shadow-sm'
        : 'text-muted-foreground hover:bg-gradient-to-r hover:from-muted hover:to-muted/80 dark:hover:from-muted/30 dark:hover:to-muted/20'
    ]"
    @click="handleClick"
  >
    <Checkbox
      v-if="selectionMode"
      :model-value="checked"
      :disabled="disabled"
      class="flex-shrink-0 cursor-pointer"
      @click.stop.prevent="handleCheckboxClick"
    />
    <component :is="iconComponent" class="h-4 w-4 flex-shrink-0 text-primary-600" />
    <span class="truncate text-foreground text-sm flex-1 min-w-0">{{ label }}</span>
    <span
      v-if="selectionMode && status"
      class="rounded-full bg-primary-100 px-2 py-0.5 text-xs font-medium text-primary-700 flex-shrink-0 whitespace-nowrap"
    >
      {{ status }}
    </span>
    <span
      v-if="!selectionMode && meta"
      class="text-xs text-muted-foreground flex-shrink-0 whitespace-nowrap"
    >
      {{ meta }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { Checkbox } from '@/components/ui/checkbox'
import { Columns3 } from 'lucide-vue-next'
import { computed } from 'vue'

const props = defineProps<{
  label: string
  isSelected?: boolean
  meta?: string
  selectionMode?: boolean
  checked?: boolean
  disabled?: boolean
  status?: string
}>()

const emit = defineEmits<{
  (e: 'select'): void
  (e: 'toggle-check'): void
}>()

const iconComponent = computed(() => Columns3)

function handleClick() {
  // In selection mode, clicking the line does nothing (only checkbox works)
  // In normal mode, select the asset
  if (!props.selectionMode) {
    emit('select')
  }
}

function handleCheckboxClick() {
  emit('toggle-check')
}
</script>
