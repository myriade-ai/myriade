<template>
  <div
    class="flex flex-col gap-3 lg:gap-4 lg:grid lg:grid-cols-[1fr_auto_auto_auto_auto] lg:items-center flex-shrink-0 p-4 border-b border-slate-200 bg-gradient-to-r from-slate-50 via-stone-50 to-slate-50"
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
            v-if="isSearching && searchQuery.length >= 3"
            class="absolute right-3 top-1/2 -translate-y-1/2"
          >
            <svg
              class="animate-spin h-4 w-4 text-gray-400"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
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
          <SelectItem value="validated">Validated</SelectItem>
          <SelectItem value="human_authored">Human authored</SelectItem>
          <SelectItem value="published_by_ai">Published by AI</SelectItem>
          <SelectItem value="needs_review">Needs review</SelectItem>
          <SelectItem value="requires_validation">Requires validation</SelectItem>
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
