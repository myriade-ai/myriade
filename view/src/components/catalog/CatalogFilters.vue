<template>
  <div
    class="flex flex-col gap-3 flex-shrink-0 border-b border-border bg-gradient-to-r from-muted/50 via-muted/30 to-muted/50 dark:from-muted/20 dark:via-muted/10 dark:to-muted/20"
  >
    <!-- Search Row -->
    <div class="flex w-full flex-wrap items-center gap-2 p-4 pb-0">
      <Button
        v-if="showExplorerShortcut"
        variant="outline"
        size="sm"
        class="flex items-center gap-2 w-full lg:w-auto justify-center lg:justify-start"
        @click="$emit('open-explorer')"
      >
        <PanelLeft class="size-4" />
        <span>Explorer</span>
      </Button>
      <!-- Collapsed Explorer Toggle Button -->
      <Button
        v-if="explorerCollapsed && !showExplorerShortcut"
        variant="ghost"
        size="icon"
        @click="$emit('toggle-explorer')"
        title="Expand explorer"
      >
        <ChevronsRight />
      </Button>
      <div class="flex min-w-0 flex-1 items-center gap-2 w-full">
        <div class="relative flex-1 min-w-0">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            :model-value="searchQuery"
            @update:model-value="(value) => $emit('update:searchQuery', String(value))"
            placeholder="Search tables, columns, descriptions..."
            class="w-full min-w-0 pl-9"
          />
          <!-- Loading indicator for server-side search -->
          <div
            v-if="isSearching && searchQuery.length > 0"
            class="absolute right-3 top-1/2 -translate-y-1/2"
          >
            <LoaderIcon :width="40" :height="20" />
          </div>
        </div>
        <Button
          variant="outline"
          size="icon"
          class="shrink-0"
          @click="$emit('clear-filters')"
          :disabled="!hasActiveFilters"
          title="Clear all filters"
        >
          <X class="h-4 w-4" />
          <span class="sr-only">Clear filters</span>
        </Button>
      </div>
    </div>

    <!-- Quick Filter Chips Row -->
    <div class="flex items-center gap-2 px-4 pb-3 overflow-x-auto">
      <!-- AI Suggestions Quick Filter -->
      <button
        @click="toggleAiSuggestionFilter"
        :class="[
          'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 whitespace-nowrap border',
          hasAiSuggestion === 'true'
            ? 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 border-purple-300 dark:border-purple-700 shadow-sm'
            : 'bg-background hover:bg-muted/60 text-muted-foreground hover:text-foreground border-border'
        ]"
      >
        <Sparkles class="h-3.5 w-3.5" />
        <span>Myriade Suggestions</span>
        <Badge
          v-if="aiSuggestionCount > 0"
          variant="secondary"
          :class="[
            'ml-0.5 h-5 min-w-5 px-1.5 text-[10px] rounded-full',
            hasAiSuggestion === 'true'
              ? 'bg-purple-200 dark:bg-purple-800 text-purple-800 dark:text-purple-200'
              : ''
          ]"
        >
          {{ aiSuggestionCount }}
        </Badge>
      </button>

      <!-- Needs Review Quick Filter (Draft status) -->
      <button
        @click="toggleStatusFilter('draft')"
        :class="[
          'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 whitespace-nowrap border',
          selectedStatus === 'draft'
            ? 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-700 shadow-sm'
            : 'bg-background hover:bg-muted/60 text-muted-foreground hover:text-foreground border-border'
        ]"
      >
        <PencilLine class="h-3.5 w-3.5" />
        <span>Drafts</span>
        <Badge
          v-if="draftCount > 0"
          variant="secondary"
          :class="[
            'ml-0.5 h-5 min-w-5 px-1.5 text-[10px] rounded-full',
            selectedStatus === 'draft'
              ? 'bg-amber-200 dark:bg-amber-800 text-amber-800 dark:text-amber-200'
              : ''
          ]"
        >
          {{ draftCount }}
        </Badge>
      </button>

      <!-- Published Quick Filter -->
      <button
        @click="toggleStatusFilter('published')"
        :class="[
          'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 whitespace-nowrap border',
          selectedStatus === 'published'
            ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 border-green-300 dark:border-green-700 shadow-sm'
            : 'bg-background hover:bg-muted/60 text-muted-foreground hover:text-foreground border-border'
        ]"
      >
        <CheckCircle2 class="h-3.5 w-3.5" />
        <span>Published</span>
        <Badge
          v-if="publishedCount > 0"
          variant="secondary"
          :class="[
            'ml-0.5 h-5 min-w-5 px-1.5 text-[10px] rounded-full',
            selectedStatus === 'published'
              ? 'bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200'
              : ''
          ]"
        >
          {{ publishedCount }}
        </Badge>
      </button>

      <!-- Unverified Quick Filter -->
      <button
        @click="toggleStatusFilter('unverified')"
        :class="[
          'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 whitespace-nowrap border',
          selectedStatus === 'unverified'
            ? 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-400 dark:border-gray-500 shadow-sm'
            : 'bg-background hover:bg-muted/60 text-muted-foreground hover:text-foreground border-border'
        ]"
      >
        <CircleDashed class="h-3.5 w-3.5" />
        <span>Unverified</span>
        <Badge
          v-if="unverifiedCount > 0"
          variant="secondary"
          :class="[
            'ml-0.5 h-5 min-w-5 px-1.5 text-[10px] rounded-full',
            selectedStatus === 'unverified'
              ? 'bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200'
              : ''
          ]"
        >
          {{ unverifiedCount }}
        </Badge>
      </button>

      <!-- Divider -->
      <div class="h-6 w-px bg-border mx-1" />

      <!-- Tags Dropdown -->
      <Select
        :model-value="selectedTag"
        @update:model-value="(value) => $emit('update:selectedTag', String(value || '__all__'))"
      >
        <SelectTrigger
          :class="[
            'w-auto min-w-[120px] h-8 text-xs rounded-full border',
            selectedTag && selectedTag !== '__all__'
              ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-700'
              : 'bg-background border-border'
          ]"
        >
          <div class="flex items-center gap-1.5">
            <Tag class="h-3.5 w-3.5" />
            <SelectValue placeholder="All tags" />
          </div>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">All tags</SelectItem>
          <SelectItem v-for="tag in tagOptions" :key="tag.id" :value="tag.id">
            {{ tag.name }}
          </SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- Active Filters Summary (shown when filters are active) -->
    <div
      v-if="hasActiveFilters && activeFiltersSummary.length > 0"
      class="flex items-center gap-2 px-4 pb-3 -mt-1"
    >
      <span class="text-xs text-muted-foreground">Active:</span>
      <div class="flex flex-wrap items-center gap-1.5">
        <button
          v-for="filter in activeFiltersSummary"
          :key="filter.key"
          @click="clearFilter(filter.key)"
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
        >
          <span>{{ filter.label }}</span>
          <X class="h-3 w-3" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import type { AssetTag } from '@/stores/catalog'
import {
  CheckCircle2,
  ChevronsRight,
  CircleDashed,
  PanelLeft,
  PencilLine,
  Search,
  Sparkles,
  Tag,
  X
} from 'lucide-vue-next'
import { computed } from 'vue'
import LoaderIcon from '../icons/LoaderIcon.vue'

interface Props {
  searchQuery: string
  selectedDatabase: string
  selectedSchema: string
  selectedTag: string
  selectedStatus: string
  hasAiSuggestion: string
  databaseOptions: string[]
  schemaOptions: string[]
  tagOptions: AssetTag[]
  hasActiveFilters: boolean
  explorerCollapsed: boolean
  showExplorerShortcut?: boolean
  isSearching?: boolean
  // Stats for filter counts
  aiSuggestionCount?: number
  draftCount?: number
  publishedCount?: number
  unverifiedCount?: number
}

const props = withDefaults(defineProps<Props>(), {
  showExplorerShortcut: false,
  isSearching: false,
  aiSuggestionCount: 0,
  draftCount: 0,
  publishedCount: 0,
  unverifiedCount: 0
})

const emit = defineEmits<{
  'update:searchQuery': [value: string]
  'update:selectedDatabase': [value: string]
  'update:selectedSchema': [value: string]
  'update:selectedTag': [value: string]
  'update:selectedStatus': [value: string]
  'update:hasAiSuggestion': [value: string]
  'clear-filters': []
  'toggle-explorer': []
  'open-explorer': []
}>()

// Toggle functions for quick filters
function toggleAiSuggestionFilter() {
  const newValue = props.hasAiSuggestion === 'true' ? '__all__' : 'true'
  emit('update:hasAiSuggestion', newValue)
}

function toggleStatusFilter(status: string) {
  const newValue = props.selectedStatus === status ? '__all__' : status
  emit('update:selectedStatus', newValue)
}

// Active filters summary for removable chips
const activeFiltersSummary = computed(() => {
  const filters: { key: string; label: string }[] = []

  if (props.searchQuery.trim()) {
    filters.push({ key: 'search', label: `"${props.searchQuery}"` })
  }

  if (props.hasAiSuggestion === 'true') {
    filters.push({ key: 'ai', label: 'Myriade Suggestions' })
  }

  if (props.selectedStatus && props.selectedStatus !== '__all__') {
    const statusLabels: Record<string, string> = {
      draft: 'Drafts',
      published: 'Published',
      unverified: 'Unverified'
    }
    filters.push({
      key: 'status',
      label: statusLabels[props.selectedStatus] || props.selectedStatus
    })
  }

  if (props.selectedTag && props.selectedTag !== '__all__') {
    const tag = props.tagOptions.find((t) => t.id === props.selectedTag)
    filters.push({ key: 'tag', label: tag?.name || 'Tag' })
  }

  return filters
})

function clearFilter(key: string) {
  switch (key) {
    case 'search':
      emit('update:searchQuery', '')
      break
    case 'ai':
      emit('update:hasAiSuggestion', '__all__')
      break
    case 'status':
      emit('update:selectedStatus', '__all__')
      break
    case 'tag':
      emit('update:selectedTag', '__all__')
      break
  }
}
</script>
