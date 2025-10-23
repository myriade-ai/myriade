<template>
  <div
    class="grid gap-2 lg:grid-cols-[1fr_auto_auto_auto_auto] items-center flex-shrink-0 p-4 border-b border-slate-200 bg-gradient-to-r from-slate-50 via-stone-50 to-slate-50"
  >
    <div class="flex flex-1 items-center gap-2">
      <!-- Collapsed Explorer Toggle Button -->
      <Button
        v-if="explorerCollapsed"
        variant="ghost"
        size="icon"
        @click="$emit('toggle-explorer')"
        title="Expand explorer"
      >
        <ChevronsRight />
      </Button>
      <Input
        :model-value="searchQuery"
        @update:model-value="(value) => $emit('update:searchQuery', String(value))"
        placeholder="Search tables, columns, descriptions..."
        class="flex-1"
      />
      <Button
        variant="outline"
        size="icon"
        @click="$emit('clear-filters')"
        :disabled="!hasActiveFilters"
      >
        <span class="sr-only">Clear filters</span>
        ✕
      </Button>
    </div>
    <Select
      :model-value="selectedSchema"
      @update:model-value="(value) => $emit('update:selectedSchema', String(value || '__all__'))"
    >
      <SelectTrigger
        :class="[
          'lg:w-44',
          selectedSchema && selectedSchema !== '__all__'
            ? 'bg-primary-600 text-white [&_svg:not([class*=\'text-\'])]:text-white '
            : ''
        ]"
      >
        <SelectValue placeholder="All schemas" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="__all__">All schemas</SelectItem>
        <SelectItem v-for="schema in schemaOptions" :key="schema" :value="schema">
          {{ schema || 'default' }}
        </SelectItem>
      </SelectContent>
    </Select>
    <Select
      :model-value="selectedTag"
      @update:model-value="(value) => $emit('update:selectedTag', String(value || '__all__'))"
    >
      <SelectTrigger
        :class="[
          'lg:w-44',
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
          'lg:w-44',
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
      </SelectContent>
    </Select>
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
import { ChevronsRight } from 'lucide-vue-next'

interface Props {
  searchQuery: string
  selectedSchema: string
  selectedTag: string
  selectedStatus: string
  schemaOptions: string[]
  tagOptions: AssetTag[]
  hasActiveFilters: boolean
  explorerCollapsed: boolean
}

defineProps<Props>()

defineEmits<{
  'update:searchQuery': [value: string]
  'update:selectedSchema': [value: string]
  'update:selectedTag': [value: string]
  'update:selectedStatus': [value: string]
  'clear-filters': []
  'toggle-explorer': []
}>()
</script>
