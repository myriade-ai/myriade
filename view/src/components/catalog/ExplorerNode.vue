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
      <div v-if="badges?.length" class="ml-4 flex flex-wrap gap-1">
        <Badge
          v-for="badge in badges"
          :key="badge.id"
          variant="secondary"
          class="text-[10px]"
          :title="badge.description || undefined"
        >
          {{ badge.name }}
        </Badge>
      </div>
    </button>
    <div v-if="expanded">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Database, FolderTree, Table as TableIcon, ChevronRight } from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import type { AssetTag } from '@/stores/catalog'

const props = defineProps<{
  label: string
  icon: 'database' | 'schema' | 'table'
  expanded: boolean
  isSelected?: boolean
  badges?: AssetTag[]
}>()

const emit = defineEmits<{
  (e: 'toggle'): void
  (e: 'select'): void
}>()

const iconComponent = computed(() => {
  if (props.icon === 'database') return Database
  if (props.icon === 'table') return TableIcon
  return FolderTree
})

function handleSelect() {
  // Always emit 'select' for row clicks
  // The chevron handles toggling separately via @click.stop on the ChevronRight icon
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
