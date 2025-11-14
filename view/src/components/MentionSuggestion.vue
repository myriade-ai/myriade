<template>
  <div
    ref="dropdownRef"
    class="z-50 w-[36rem] max-h-72 overflow-y-auto bg-white border border-gray-200 rounded-lg shadow-lg"
  >
    <!-- Loading state -->
    <div v-if="isLoading" class="p-4 text-center text-sm text-gray-500">
      <Loader2 class="inline-block w-4 h-4 animate-spin mr-2" />
      Loading...
    </div>

    <!-- Empty state -->
    <div v-else-if="displayedItems.length === 0" class="p-4 text-center text-sm text-gray-500">
      No queries or charts found
    </div>

    <!-- Mentions list -->
    <div v-else class="py-2">
      <!-- Show section header for recent items when not searching -->
      <div v-if="!hasSearch" class="px-3 py-1 text-xs font-medium text-gray-500 uppercase">
        Recent
      </div>
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
          <component
            :is="item.type === 'query' ? FileCode : BarChart3"
            class="w-4 h-4 mt-0.5 flex-shrink-0"
            :class="item.type === 'query' ? 'text-blue-600' : 'text-green-600'"
          />
          <div class="flex-1 min-w-0 leading-normal">
            <div class="font-medium text-sm truncate text-black">{{ item.title }}</div>
            <div v-if="item.type === 'query' && item.sql" class="text-xs text-gray-500 truncate">
              {{ item.sql }}
            </div>
          </div>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  useRecentMentionsQuery,
  useSearchMentionsQuery,
  type MentionItem
} from '@/composables/useDocumentMentions'
import { debounce } from '@/utils/debounce'
import { BarChart3, FileCode, Loader2 } from 'lucide-vue-next'
import { computed, nextTick, ref, watch } from 'vue'

interface Props {
  query: string
  command: (item: MentionItem) => void
}

const props = defineProps<Props>()

const dropdownRef = ref<HTMLDivElement | null>(null)
const selectedIndex = ref(0)

// Debounced search query for TanStack Query
const debouncedSearchQuery = ref(props.query)

// Update debounced search with 200ms delay
const updateDebouncedSearch = debounce((value: string) => {
  debouncedSearchQuery.value = value
}, 200)

watch(
  () => props.query,
  (newQuery) => {
    updateDebouncedSearch(newQuery)
  },
  { immediate: true }
)

// Use recent mentions query when no search, otherwise use search query
const hasSearch = computed(() => debouncedSearchQuery.value.trim() !== '')

// Fetch recent mentions (backend-provided, last 10 items sorted by updatedAt)
const { data: recentData, isLoading: isLoadingRecent } = useRecentMentionsQuery()

// Fetch search results with debounced search using TanStack Query
const searchRef = computed(() => debouncedSearchQuery.value)
const { data: searchData, isLoading: isLoadingSearch } = useSearchMentionsQuery(searchRef)

// Determine which data to display
const displayedItems = computed(() => {
  if (hasSearch.value) {
    return searchData.value || []
  }
  return recentData.value || []
})

const isLoading = computed(() => {
  if (hasSearch.value) {
    return isLoadingSearch.value
  }
  return isLoadingRecent.value
})

// Reset selectedIndex when items change (like in official TipTap example)
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
