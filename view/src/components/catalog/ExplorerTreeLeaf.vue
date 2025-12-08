<template>
  <div
    class="flex w-full items-center gap-2 rounded-lg pl-5 pr-2 py-1.5 text-left text-sm transition-all duration-200"
    :class="[
      props.mode !== 'select' ? 'cursor-pointer' : '',
      isSelected
        ? 'bg-gradient-to-r from-primary-50 to-muted dark:from-primary-900/30 dark:to-muted/30 text-primary-900 dark:text-primary-100 ring-1 ring-primary-400 shadow-sm'
        : 'text-muted-foreground hover:bg-gradient-to-r hover:from-muted hover:to-muted/80 dark:hover:from-muted/30 dark:hover:to-muted/20'
    ]"
    @click="handleClick"
  >
    <!-- Checkbox (select mode only) -->
    <Checkbox
      v-if="props.mode === 'select'"
      :model-value="checked"
      :disabled="disabled"
      class="flex-shrink-0 cursor-pointer"
      @click.stop.prevent="handleCheckboxClick"
    />

    <!-- Icon -->
    <Columns3 class="h-4 w-4 flex-shrink-0 text-primary-600" />

    <!-- Label -->
    <span class="truncate text-foreground text-sm flex-1 min-w-0">{{ label }}</span>

    <!-- Status Badge -->
    <StatusBadge v-if="statusInfo" :status="statusInfo" class="flex-shrink-0" />
  </div>
</template>

<script setup lang="ts">
import StatusBadge from '@/components/catalog/StatusBadge.vue'
import { Checkbox } from '@/components/ui/checkbox'
import { Columns3 } from 'lucide-vue-next'
import type { AssetStatusInfo, ExplorerMode } from './types'

interface Props {
  label: string
  isSelected?: boolean
  mode?: ExplorerMode
  checked?: boolean
  disabled?: boolean
  statusInfo?: AssetStatusInfo
}

const props = withDefaults(defineProps<Props>(), {
  isSelected: false,
  mode: 'browse',
  checked: false,
  disabled: false
})

const emit = defineEmits<{
  (e: 'select'): void
  (e: 'toggle-check'): void
}>()

function handleClick() {
  // In selection mode, clicking the line does nothing (only checkbox works)
  // In browse/editor mode, select the asset
  if (props.mode !== 'select') {
    emit('select')
  }
}

function handleCheckboxClick() {
  emit('toggle-check')
}
</script>
