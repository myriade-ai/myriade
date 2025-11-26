<template>
  <div
    class="flex flex-col gap-3 lg:gap-4 lg:grid lg:grid-cols-[1fr_auto_auto_auto_auto] lg:items-center flex-shrink-0 p-4 border-b border-border bg-gradient-to-r from-muted/50 via-muted/30 to-muted/50 dark:from-muted/20 dark:via-muted/10 dark:to-muted/20"
  >
    <!-- Search Row -->
    <div class="flex w-full flex-wrap items-center gap-2 lg:col-span-1">
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
          <Input
            :model-value="searchQuery"
            @update:model-value="(value) => $emit('update:searchQuery', String(value))"
            placeholder="Search tables, columns, descriptions..."
            class="w-full min-w-0"
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
        >
          <span class="sr-only">Clear filters</span>
          ✕
        </Button>
      </div>
    </div>

    <!-- Filter Row -->
    <div class="flex flex-col lg:flex-row gap-2 lg:col-span-4 w-full">
      <Select
        :model-value="selectedTag"
        @update:model-value="(value) => $emit('update:selectedTag', String(value || '__all__'))"
      >
        <SelectTrigger
          :class="[
            'w-full lg:w-44',
            selectedTag && selectedTag !== '__all__'
              ? 'bg-primary-600 text-white [&_svg:not([class*=\'text-\'])]:text-white '
              : ''
          ]"
        >
          <SelectValue placeholder="All tags" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">All tags</SelectItem>
          <SelectItem v-for="tag in tagOptions" :key="tag.id" :value="tag.id">
            {{ tag.name }}
          </SelectItem>
        </SelectContent>
      </Select>
      <Select
        :model-value="selectedStatus"
        @update:model-value="(value) => $emit('update:selectedStatus', String(value || '__all__'))"
      >
        <SelectTrigger
          :class="[
            'w-full lg:w-44',
            selectedStatus && selectedStatus !== '__all__'
              ? 'bg-primary-600 text-white [&_svg:not([class*=\'text-\'])]:text-white '
              : ''
          ]"
        >
          <SelectValue placeholder="All statuses" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">All statuses</SelectItem>
          <SelectItem value="draft">Draft</SelectItem>
          <SelectItem value="published">Published</SelectItem>
          <SelectItem value="unverified">Unverified</SelectItem>
        </SelectContent>
      </Select>
    </div>
  </div>
</template>

<script setup lang="ts">
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
import { ChevronsRight, PanelLeft } from 'lucide-vue-next'
import LoaderIcon from '../icons/LoaderIcon.vue'

interface Props {
  searchQuery: string
  selectedDatabase: string
  selectedSchema: string
  selectedTag: string
  selectedStatus: string
  databaseOptions: string[]
  schemaOptions: string[]
  tagOptions: AssetTag[]
  hasActiveFilters: boolean
  explorerCollapsed: boolean
  showExplorerShortcut?: boolean
  isSearching?: boolean
}

defineProps<Props>()

defineEmits<{
  'update:searchQuery': [value: string]
  'update:selectedDatabase': [value: string]
  'update:selectedSchema': [value: string]
  'update:selectedTag': [value: string]
  'update:selectedStatus': [value: string]
  'clear-filters': []
  'toggle-explorer': []
  'open-explorer': []
}>()
</script>
