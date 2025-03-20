<template>
  <div class="w-72">
    <Combobox v-model="selected" multiple immediate>
      <div class="relative mt-1">
        <div
          class="relative w-full cursor-default overflow-hidden rounded-md bg-white text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-opacity-75 focus-visible:ring-offset-2 focus-visible:ring-offset-teal-300 sm:text-sm"
        >
          <ComboboxInput
            class="w-full border-gray-300 rounded-md py-2 pl-3 pr-10 text-sm text-gray-900 focus:ring-0"
            @change="query = $event.target.value"
            :displayValue="(items) => items.map((item) => item.label).join(', ')"
          />
          <ComboboxButton class="absolute inset-y-0 right-0 flex items-center pr-2">
            <ChevronUpDownIcon class="h-5 w-5 text-gray-400" aria-hidden="true" />
          </ComboboxButton>
        </div>
        <ComboboxOptions
          class="absolute mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm"
        >
          <div
            v-if="filteredGroups.length === 0 && query !== ''"
            class="relative cursor-default select-none py-2 px-4 text-gray-700"
          >
            Nothing found.
          </div>

          <div v-for="group in filteredGroups" :key="group.id" class="px-2 py-1">
            <div class="flex items-center justify-between">
              <span class="block text-sm font-medium text-gray-900">
                {{ group.label }}
              </span>
              <input
                :id="group.id"
                type="checkbox"
                :checked="isGroupSelected(group)"
                @change="toggleGroup(group)"
                class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 mr-4"
              />
            </div>
            <div class="mt-1">
              <ComboboxOption
                v-for="item in group.items"
                :key="group.id + '-' + item.id"
                :value="item"
                as="template"
                v-slot="{ active, selected: isSelected2 }"
              >
                <li
                  :class="[
                    'relative cursor-default select-none py-2 pl-3 pr-8',
                    active ? 'bg-teal-600 text-white' : 'text-gray-900'
                  ]"
                >
                  <div class="flex items-center justify-between">
                    <span :class="['block truncate', isSelected2 ? 'font-medium' : 'font-normal']">
                      {{ item.label }}
                    </span>
                    <input
                      :id="item.id"
                      type="checkbox"
                      :checked="isSelected(item)"
                      :disabled="isGroupSelected(group)"
                      :class="[
                        'absolute right-0 h-4 w-4 rounded border-gray-300 focus:ring-indigo-500',
                        isGroupSelected(group) ? 'text-gray-600' : 'text-indigo-600'
                      ]"
                    />
                  </div>
                </li>
              </ComboboxOption>
            </div>
          </div>
        </ComboboxOptions>
      </div>
    </Combobox>
  </div>
</template>

<script lang="ts"></script>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { PropType } from 'vue'

import {
  Combobox,
  ComboboxInput,
  ComboboxButton,
  ComboboxOptions,
  ComboboxOption
} from '@headlessui/vue'
import { ChevronUpDownIcon } from '@heroicons/vue/20/solid'

// Export the interfaces
export interface Item {
  id: string
  label: string
  [key: string]: any // For any additional properties
}

export interface Group {
  id: string
  label: string
  items: Item[]
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

const selected = ref<Item[]>(props.modelValue)
const query = ref('')

const filteredGroups = computed(() => {
  return props.groups
    .map((group: Group) => ({
      ...group,
      items: group.items.filter((item) =>
        Object.values(item).some((value) =>
          String(value).toLowerCase().includes(query.value.toLowerCase())
        )
      )
    }))
    .filter((group: Group) => group.items.length > 0)
})

const isSelected = (item: Item) => {
  return selected.value.some((selectedItem) => selectedItem.id === item.id)
}

const isGroupSelected = (group: Group) => {
  return group.items.every((item: Item) => isSelected(item))
}

const toggleGroup = (group: Group) => {
  const allSelected = isGroupSelected(group)
  if (allSelected) {
    selected.value = selected.value.filter(
      (item: Item) => !group.items.some((groupItem: Item) => groupItem.id === item.id)
    )
  } else {
    const newItems: Item[] = group.items.filter((item: Item) => !isSelected(item))
    selected.value.push(...newItems)
  }
}
// Add a watch effect on the modelValue prop
watch(
  () => props.modelValue,
  (newValue) => {
    selected.value = newValue
  },
  { immediate: true }
)

// Add a watch effect to emit the updated value
watch(
  selected,
  (newValue) => {
    emit('update:modelValue', newValue)
  },
  { deep: true }
)
</script>
