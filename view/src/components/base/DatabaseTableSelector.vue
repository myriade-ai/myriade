<template>
  <div class="space-y-4">
    <Input v-model="searchQuery" type="text" placeholder="Search schemas and tables..." />

    <div class="space-y-3">
      <div
        v-for="group in filteredGroups"
        :key="group.id"
        class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden"
      >
        <div
          class="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between cursor-pointer hover:bg-gray-100 transition-colors"
          @click="toggleCollapse(group.id)"
        >
          <div class="flex items-center space-x-3">
            <!-- Collapse/Expand Icon -->
            <ChevronRightIcon
              :class="[
                'h-4 w-4 text-gray-500 transition-transform',
                collapsedGroups.has(group.id) ? '' : 'rotate-90'
              ]"
            />

            <div class="flex items-center space-x-2">
              <input
                type="checkbox"
                :checked="isGroupSelected(group)"
                :indeterminate.prop="isGroupIndeterminate(group)"
                @change="toggleGroup(group)"
                @click.stop
                class="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <Label
                :for="`schema-${group.id}`"
                class="text-sm font-medium text-gray-900 cursor-pointer"
                @click.stop
              >
                {{ group.label }}
              </Label>
            </div>
          </div>

          <div v-if="getSelectedCountForGroup(group) > 0" class="flex items-center space-x-2">
            <span
              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
            >
              {{ getSelectedCountForGroup(group) }} / {{ group.items.length }} selected
            </span>
          </div>
        </div>

        <div v-show="!collapsedGroups.has(group.id)" class="divide-y divide-gray-100">
          <div
            v-for="item in group.items"
            :key="item.id"
            class="px-4 py-3 hover:bg-gray-50 transition-colors"
          >
            <div class="flex items-center space-x-3">
              <input
                :id="`table-${item.id}`"
                type="checkbox"
                :checked="isSelected(item)"
                @change="toggleItem(item)"
                class="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />

              <div class="flex-1 min-w-0">
                <Label
                  :for="`table-${item.id}`"
                  class="block text-sm font-medium text-gray-900 cursor-pointer"
                >
                  {{ item.label }}
                </Label>
                <p v-if="item.description" class="text-xs text-gray-500 mt-1 truncate">
                  {{ item.description }}
                </p>
              </div>

              <TableCellsIcon class="h-4 w-4 text-gray-400 flex-shrink-0" />
            </div>

            <div v-if="showColumnPreview(item)" class="mt-2 ml-7">
              <div class="text-xs text-gray-500 space-y-1">
                <div class="font-medium">Columns:</div>
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="column in getItemColumns(item)"
                    :key="column.name"
                    class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700"
                  >
                    {{ column.name }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="filteredGroups.length === 0"
        class="text-center py-4 border border-gray-200 bg-gray-200 rounded-lg shadow-sm overflow-hidden"
      >
        <div class="text-sm text-gray-500">No tables found</div>
      </div>
    </div>

    <!-- Selection Summary -->
    <div
      v-if="modelValue.length > 0"
      class="mt-4 p-3 bg-primary-50 rounded-lg border border-primary-200"
    >
      <div class="flex items-center space-x-2">
        <CheckCircleIcon class="h-5 w-5 text-primary-600" />
        <span class="text-sm font-medium text-primary-900">
          {{ modelValue.length }} table{{ modelValue.length !== 1 ? 's' : '' }} selected
        </span>
      </div>
      <div class="mt-2 text-xs text-primary-700">
        {{ getSelectionSummary() }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CheckCircleIcon, ChevronRightIcon, TableCellsIcon } from '@heroicons/vue/24/outline'
import type { PropType } from 'vue'
import { computed, ref } from 'vue'
import { Input } from '../ui/input'
import Label from '../ui/label/Label.vue'

export interface Item {
  id: string
  label: string
  description?: string
  [key: string]: unknown
  columns?: TableColumn[]
}

export interface Group {
  id: string
  label: string
  items: Item[]
}

interface TableColumn {
  name: string
  description?: string
}

const props = defineProps({
  groups: {
    type: Array as PropType<Group[]>,
    required: true,
    default: () => []
  },
  modelValue: {
    type: Array as PropType<Item[]>,
    required: true,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const searchQuery = ref('')
const collapsedGroups = ref<Set<string>>(new Set())

const filteredGroups = computed(() => {
  if (!searchQuery.value.trim()) {
    return props.groups
  }

  const query = searchQuery.value.toLowerCase()
  return props.groups
    .map((group) => ({
      ...group,
      items: group.items.filter(
        (item) =>
          item.label.toLowerCase().includes(query) ||
          item.description?.toLowerCase().includes(query) ||
          group.label.toLowerCase().includes(query)
      )
    }))
    .filter((group) => group.items.length > 0)
})

const isSelected = (item: Item): boolean => {
  return props.modelValue.some((selectedItem) => selectedItem.id === item.id)
}

const isGroupSelected = (group: Group): boolean => {
  return group.items.length > 0 && group.items.every((item) => isSelected(item))
}

const isGroupIndeterminate = (group: Group): boolean => {
  const selectedCount = group.items.filter((item) => isSelected(item)).length
  return selectedCount > 0 && selectedCount < group.items.length
}

const getSelectedCountForGroup = (group: Group): number => {
  return group.items.filter((item) => isSelected(item)).length
}

const toggleItem = (item: Item) => {
  if (isSelected(item)) {
    emit(
      'update:modelValue',
      props.modelValue.filter((selectedItem) => selectedItem.id !== item.id)
    )
  } else {
    emit('update:modelValue', [...props.modelValue, item])
  }
}

const toggleGroup = (group: Group) => {
  if (isGroupSelected(group)) {
    const newSelection = props.modelValue.filter(
      (selectedItem) => !group.items.some((groupItem) => groupItem.id === selectedItem.id)
    )
    emit('update:modelValue', newSelection)
  } else {
    const newItems = group.items.filter((item) => !isSelected(item))
    emit('update:modelValue', [...props.modelValue, ...newItems])
  }
}

const toggleCollapse = (groupId: string) => {
  if (collapsedGroups.value.has(groupId)) {
    collapsedGroups.value.delete(groupId)
  } else {
    collapsedGroups.value.add(groupId)
  }
}

const showColumnPreview = (item: Item): boolean => {
  return Array.isArray(item.columns) && (item.columns?.length ?? 0) > 0
}

const getItemColumns = (item: Item): TableColumn[] => {
  return item.columns || []
}

const getSelectionSummary = (): string => {
  const groupCounts = new Map<string, number>()

  props.modelValue.forEach((item) => {
    const group = props.groups.find((g) => g.items.some((i) => i.id === item.id))
    if (group) {
      groupCounts.set(group.label, (groupCounts.get(group.label) || 0) + 1)
    }
  })

  return Array.from(groupCounts.entries())
    .map(([groupLabel, count]) => `${groupLabel}: ${count}`)
    .join(', ')
}
</script>
