<template>
  <div class="sm:block">
    <TabGroup :selectedIndex="selectedIndex" @change="changeTab">
      <TabList class="text-sm border-b border-gray-200 -mb-px flex space-x-4">
        <Tab v-for="(tab, ind) in tabs" as="template" :key="ind" v-slot="{ selected }">
          <button
            :class="[
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-md',
              selected
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            {{ tab }}
          </button>
        </Tab>
      </TabList>
    </TabGroup>
  </div>
</template>

<script setup lang="ts">
import { TabGroup, TabList, Tab } from '@headlessui/vue'
import { computed } from 'vue'

const emit = defineEmits(['change'])

const props = defineProps({
  tabs: {
    type: Array,
    required: true
  },
  selected: {
    type: String,
    default: null
  }
})

const selectedIndex = computed(() => {
  return props.tabs.indexOf(props.selected)
})

function changeTab(index) {
  const selected = props.tabs[index]
  emit('change', selected)
}
</script>
