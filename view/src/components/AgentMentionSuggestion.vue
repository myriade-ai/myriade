<template>
  <div
    ref="dropdownRef"
    class="z-50 w-64 max-h-72 overflow-y-auto bg-white border border-gray-200 rounded-lg shadow-lg"
  >
    <!-- Loading state (kept for consistency, though we don't fetch data) -->
    <div v-if="isLoading" class="p-4 text-center text-sm text-gray-500">
      <Loader2 class="inline-block w-4 h-4 animate-spin mr-2" />
      Loading...
    </div>

    <!-- Empty state when query doesn't match -->
    <div v-else-if="displayedItems.length === 0" class="p-4 text-center text-sm text-gray-500">
      No matches found
    </div>

    <!-- Agent option -->
    <div v-else class="py-2">
      <button
        v-for="(item, index) in displayedItems"
        :key="item.id"
        @click="selectItem(index)"
        @mouseenter="selectedIndex = index"
        :class="[
          'w-full text-left px-3 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none transition-colors',
          selectedIndex === index && 'bg-gray-100'
        ]"
      >
        <div class="flex items-start gap-2">
          <SparklesIcon class="w-4 h-4 mt-0.5 flex-shrink-0 text-purple-600" />
          <div class="flex-1 min-w-0 leading-normal">
            <div class="font-medium text-sm text-black">{{ item.label }}</div>
            <div class="text-xs text-gray-500">{{ item.description }}</div>
          </div>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Loader2, SparklesIcon } from 'lucide-vue-next'
import { computed, nextTick, ref, watch } from 'vue'
import type { BaseMentionItem } from './editor/mentions'

// Agent mention item type
interface AgentMentionItem extends BaseMentionItem {
  label: string
  description: string
}

interface Props {
  query: string
  command: (item: AgentMentionItem) => void
}

const props = defineProps<Props>()

const dropdownRef = ref<HTMLDivElement | null>(null)
const selectedIndex = ref(0)
const isLoading = ref(false)

// Static list of agent options
const agentItems: AgentMentionItem[] = [
  {
    id: 'myriade-agent',
    type: 'agent',
    label: 'Myriade Agent',
    description: 'Ask AI to analyze this asset'
  }
]

// Filter items based on query
const displayedItems = computed(() => {
  const query = props.query.toLowerCase().trim()
  if (!query) {
    return agentItems
  }
  return agentItems.filter(
    (item) =>
      item.label.toLowerCase().includes(query) ||
      item.id.toLowerCase().includes(query) ||
      item.description.toLowerCase().includes(query)
  )
})

// Reset selectedIndex when items change
watch(
  () => displayedItems.value,
  () => {
    selectedIndex.value = 0
  }
)

// Keyboard navigation (like in official TipTap example)
function onKeyDown({ event }: { event: KeyboardEvent }): boolean {
  if (event.key === 'ArrowUp') {
    selectedIndex.value =
      (selectedIndex.value + displayedItems.value.length - 1) % displayedItems.value.length
    scrollToSelected()
    return true
  }

  if (event.key === 'ArrowDown') {
    selectedIndex.value = (selectedIndex.value + 1) % displayedItems.value.length
    scrollToSelected()
    return true
  }

  if (event.key === 'Enter') {
    selectItem(selectedIndex.value)
    return true
  }

  return false
}

function selectItem(index: number) {
  const item = displayedItems.value[index]
  if (item) {
    props.command(item)
  }
}

function scrollToSelected() {
  nextTick(() => {
    if (!dropdownRef.value) return

    const selectedElement = dropdownRef.value.querySelector('.bg-gray-100') as HTMLElement | null
    if (selectedElement) {
      selectedElement.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  })
}

// Expose methods for parent component (like in official TipTap example)
defineExpose({
  onKeyDown
})
</script>
