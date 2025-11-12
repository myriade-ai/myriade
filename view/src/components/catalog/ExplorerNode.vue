<template>
  <div>
    <div
      class="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm font-medium transition-all duration-200"
      :class="[
        isSelected
          ? 'bg-gradient-to-r from-blue-50 to-slate-100 text-primary-900 ring-1 ring-primary-400 shadow-sm'
          : 'text-foreground hover:bg-gradient-to-r hover:from-slate-100 hover:to-stone-100'
      ]"
      @click="handleLineClick"
    >
      <Checkbox
        v-if="selectionMode"
        :model-value="checked"
        :disabled="disabled"
        class="flex-shrink-0 cursor-pointer"
        @click.stop.prevent="handleCheckboxClick"
      />
      <ChevronRight
        class="h-4 w-4 flex-shrink-0 text-muted-foreground cursor-pointer"
        :class="expanded ? 'rotate-90' : ''"
      />
      <component :is="iconComponent" class="h-4 w-4 flex-shrink-0 text-primary-600" />
      <span class="truncate text-sm flex-1 min-w-0">{{ label }}</span>
      <span
        v-if="selectionMode && status"
        class="rounded-full bg-primary-100 px-2 py-0.5 text-xs font-medium text-primary-700 flex-shrink-0 whitespace-nowrap"
      >
        {{ status }}
      </span>
      <span
        v-if="selectionMode && childCount && childType"
        class="text-xs text-muted-foreground flex-shrink-0 whitespace-nowrap"
      >
        {{ childCount }} {{ childType }}
      </span>
    </div>
    <div v-if="expanded">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Checkbox } from '@/components/ui/checkbox'
import {
  ChevronRight,
  Database,
  FolderTree,
  Table as TableIcon,
  View as ViewIcon
} from 'lucide-vue-next'
import { computed } from 'vue'

const props = defineProps<{
  label: string
  icon: 'database' | 'schema' | 'table' | 'view'
  expanded: boolean
  isSelected?: boolean
  selectionMode?: boolean
  checked?: boolean
  disabled?: boolean
  status?: string
  childCount?: number
  childType?: string
}>()

const emit = defineEmits<{
  (e: 'toggle'): void
  (e: 'select'): void
  (e: 'toggle-check'): void
}>()

const iconComponent = computed(() => {
  if (props.icon === 'database') return Database
  if (props.icon === 'table') return TableIcon
  if (props.icon === 'view') return ViewIcon
  return FolderTree
})

function handleLineClick() {
  if (props.selectionMode) {
    // In selection mode, toggle expand/collapse
    emit('toggle')
  } else {
    // In normal mode, toggle expand/collapse AND select the asset
    emit('toggle')
    emit('select')
  }
}

function handleCheckboxClick() {
  emit('toggle-check')
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
