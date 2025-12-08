<template>
  <div>
    <div
      class="group flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm font-medium transition-all duration-200 cursor-pointer"
      :class="[
        isSelected
          ? 'bg-gradient-to-r from-primary-50 to-muted dark:from-primary-900/30 dark:to-muted/30 text-primary-900 dark:text-primary-100 ring-1 ring-primary-400 shadow-sm'
          : isUsed
            ? 'bg-primary-50/50 dark:bg-primary-900/20 text-foreground'
            : 'text-foreground hover:bg-gradient-to-r hover:from-muted hover:to-muted/80 dark:hover:from-muted/30 dark:hover:to-muted/20'
      ]"
      @click="handleLineClick"
    >
      <!-- Checkbox (select mode only) -->
      <Checkbox
        v-if="props.mode === 'select'"
        :model-value="checked"
        :disabled="disabled"
        class="flex-shrink-0 cursor-pointer"
        @click.stop.prevent="handleCheckboxClick"
      />

      <!-- Expand/Collapse chevron -->
      <ChevronRight
        class="h-4 w-4 flex-shrink-0 text-muted-foreground cursor-pointer transition-transform duration-200"
        :class="expanded ? 'rotate-90' : ''"
      />

      <!-- Icon -->
      <component :is="iconComponent" class="h-4 w-4 flex-shrink-0 text-primary-600" />

      <!-- Label -->
      <span class="truncate text-sm flex-1 min-w-0" :class="{ 'font-semibold': isUsed }">
        {{ label }}
      </span>

      <!-- Status Badge -->
      <StatusBadge v-if="statusInfo" :status="statusInfo" class="flex-shrink-0" />

      <!-- Child count (select mode) -->
      <span
        v-if="props.mode === 'select' && childCount && childType"
        class="text-xs text-muted-foreground flex-shrink-0 whitespace-nowrap"
      >
        {{ childCount }} {{ childType }}
      </span>

      <!-- Quick Actions (editor mode) -->
      <div
        v-if="showQuickActions"
        class="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger as-child>
              <Button
                variant="ghost"
                size="icon"
                class="h-6 w-6"
                @click.stop="handleQuickAction('select-all')"
              >
                <Search class="h-3.5 w-3.5 text-muted-foreground" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>SELECT * FROM table</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </div>

    <!-- Children slot -->
    <div v-if="expanded">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import StatusBadge from '@/components/catalog/StatusBadge.vue'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import {
  ChevronRight,
  Database,
  FolderTree,
  Search,
  Table as TableIcon,
  View as ViewIcon
} from 'lucide-vue-next'
import { computed } from 'vue'
import type { AssetStatusInfo, ExplorerMode } from './types'

interface Props {
  label: string
  icon: 'database' | 'schema' | 'table' | 'view'
  expanded: boolean
  isSelected?: boolean
  mode?: ExplorerMode
  checked?: boolean
  disabled?: boolean
  statusInfo?: AssetStatusInfo
  childCount?: number
  childType?: string
  isUsed?: boolean
  showQuickActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isSelected: false,
  mode: 'browse',
  checked: false,
  disabled: false,
  isUsed: false,
  showQuickActions: false
})

const emit = defineEmits<{
  (e: 'toggle'): void
  (e: 'select'): void
  (e: 'toggle-check'): void
  (e: 'quick-action', action: string): void
}>()

const iconComponent = computed(() => {
  if (props.icon === 'database') return Database
  if (props.icon === 'table') return TableIcon
  if (props.icon === 'view') return ViewIcon
  return FolderTree
})

function handleLineClick() {
  if (props.mode === 'select') {
    // In selection mode, toggle expand/collapse
    emit('toggle')
  } else {
    // In browse/editor mode, toggle expand/collapse AND select the asset
    emit('toggle')
    emit('select')
  }
}

function handleCheckboxClick() {
  emit('toggle-check')
}

function handleQuickAction(action: string) {
  emit('quick-action', action)
}
</script>
