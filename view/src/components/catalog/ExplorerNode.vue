<template>
  <div>
    <button
      type="button"
      class="flex w-full flex-col items-start gap-1 rounded-lg px-2 py-1.5 text-left text-sm font-medium transition-all duration-200"
      :class="[
        isSelected
          ? 'bg-gradient-to-r from-blue-50 to-slate-100 text-primary-900 ring-1 ring-primary-400 shadow-sm'
          : 'text-foreground hover:bg-gradient-to-r hover:from-slate-100 hover:to-stone-100'
      ]"
      @click.stop="handleSelect"
    >
      <div class="flex w-full items-center gap-2">
        <ChevronRight
          class="h-4 w-4 flex-shrink-0 text-muted-foreground cursor-pointer"
          :class="expanded ? 'rotate-90' : ''"
          @click.stop="emit('toggle')"
        />
        <component :is="iconComponent" class="h-4 w-4 flex-shrink-0 text-primary-600" />
        <span class="break-words">{{ label }}</span>
      </div>
    </button>
    <div v-if="expanded">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
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
}>()

const emit = defineEmits<{
  (e: 'toggle'): void
  (e: 'select'): void
}>()

const iconComponent = computed(() => {
  if (props.icon === 'database') return Database
  if (props.icon === 'table') return TableIcon
  if (props.icon === 'view') return ViewIcon
  return FolderTree
})

function handleSelect() {
  emit('select')
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
