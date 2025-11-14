<template>
  <div
    ref="dropdownRef"
    class="z-50 w-[36rem] max-h-72 overflow-y-auto bg-white border border-gray-200 rounded-lg shadow-lg py-2"
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
      <!-- Recent section -->
      <div v-if="recentMentions.length > 0 && !props.query.trim()">
        <div class="px-3 py-1 text-xs font-medium text-gray-500 uppercase">Recent</div>
        <button
          v-for="(item, index) in recentMentions"
          :key="`recent-${item.id}`"
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
            <div class="flex-1 min-w-0">
              <div class="font-medium text-sm truncate text-black">{{ item.title }}</div>
              <div v-if="item.type === 'query' && item.sql" class="text-xs text-gray-500 truncate">
                {{ item.sql }}
              </div>
            </div>
          </div>
        </button>
        <div v-if="otherMentions.length > 0" class="my-2 border-t border-gray-200"></div>
      </div>

      <!-- Other mentions / All results -->
      <div v-if="otherMentions.length > 0">
        <div
          v-if="recentMentions.length > 0 && !props.query.trim()"
          class="px-3 py-1 text-xs font-medium text-gray-500 uppercase"
        >
          All Items
        </div>
        <button
          v-for="(item, index) in otherMentions"
          :key="item.id"
          @click="selectItem(recentMentions.length + index)"
          @mouseenter="selectedIndex = recentMentions.length + index"
          :class="[
            'w-full text-left px-3 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none transition-colors',
            selectedIndex === recentMentions.length + index && 'bg-gray-100'
          ]"
        >
          <div class="flex items-start gap-2">
            <component
              :is="item.type === 'query' ? FileCode : BarChart3"
              class="w-4 h-4 mt-0.5 flex-shrink-0"
              :class="item.type === 'query' ? 'text-blue-600' : 'text-green-600'"
            />
            <div class="flex-1 min-w-0">
              <div class="font-medium text-sm truncate text-black">{{ item.title }}</div>
              <div v-if="item.type === 'query' && item.sql" class="text-xs text-gray-500 truncate">
                {{ item.sql }}
              </div>
            </div>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  getRecentMentions,
  mergeWithRecent,
  useMentionsQuery,
  type MentionItem
} from '@/composables/useDocumentMentions'
import { useContextsStore } from '@/stores/contexts'
import { debounce } from '@/utils/debounce'
import { BarChart3, FileCode, Loader2 } from 'lucide-vue-next'
import { computed, nextTick, ref, watch } from 'vue'

interface Props {
  query: string
  command: (item: MentionItem) => void
}

const props = defineProps<Props>()

const contextsStore = useContextsStore()
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

// Context ID for recent mentions
const contextId = computed(() => {
  const context = contextsStore.contextSelected
  if (!context) return ''
  return context.id
})

// Fetch mentions with debounced search using TanStack Query
const searchRef = computed(() => debouncedSearchQuery.value)
const { data: mentionsData, isLoading } = useMentionsQuery(searchRef)

// Get recent mentions
const recentMentionsArray = computed(() => {
  if (!contextId.value) return []
  return getRecentMentions(contextId.value)
})

// Merge with recent mentions
const displayedItems = computed(() => {
  if (!mentionsData.value) return []
  if (props.query.trim()) {
    return mentionsData.value
  }
  return mergeWithRecent(mentionsData.value, recentMentionsArray.value)
})

// Split into recent and other for display
const recentMentions = computed(() => {
  if (props.query.trim()) return []
  return displayedItems.value.slice(0, Math.min(recentMentionsArray.value.length, 5))
})

const otherMentions = computed(() => {
  if (props.query.trim()) return displayedItems.value
  return displayedItems.value.slice(recentMentions.value.length)
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
