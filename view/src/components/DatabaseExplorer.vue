<template>
  <Card class="bg-white rounded-lg gap-0 py-2 flex flex-col h-full">
    <CardHeader class="border-b-1">
      <CardTitle class="text-xl"> Database </CardTitle>
    </CardHeader>
    <CardContent class="px-0 flex-1 overflow-hidden flex flex-col">
      <!-- Search input -->
      <div class="px-4 py-2 bg-gray-50 flex-shrink-0">
        <Input
          type="text"
          placeholder="Search table"
          id="searchTables"
          :value="searchTablesInput"
          @input="onSearchInput"
        />
      </div>

      <div v-if="isLoading && tables.length === 0" class="flex-1 overflow-y-auto p-4 space-y-3">
        <div v-for="i in 5" :key="i" class="space-y-2">
          <div class="h-4 bg-gray-200 rounded animate-pulse w-full"></div>
          <div class="h-3 bg-gray-100 rounded animate-pulse w-3/4"></div>
        </div>
      </div>

      <div v-else ref="scrollElement" class="flex-1 overflow-y-auto">
        <div v-if="visibleTables.length === 0" class="px-4 py-4 text-center text-sm text-gray-500">
          <div v-if="tables.length === 0">No table available. <br />Please contact support.</div>
          <div v-else>No tables matching search.</div>
        </div>

        <ul
          v-else
          role="list"
          :style="{ height: `${virtualizer.getTotalSize()}px` }"
          class="relative w-full"
        >
          <li
            v-for="virtualItem in virtualizer.getVirtualItems()"
            :key="`${visibleTables[virtualItem.index].name}-${visibleTables[virtualItem.index].schema}`"
            :data-index="virtualItem.index"
            :ref="(el) => measureElement(el)"
            :style="{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${virtualItem.start}px)`,
              borderBottom: '1px solid #e5e7eb'
            }"
          >
            <DatabaseExplorerItems
              :table="visibleTables[virtualItem.index]"
              :showColumns="visibleTables[virtualItem.index].name === showTableKey"
              @click="onClick(visibleTables[virtualItem.index].name)"
              @search="onSearch"
              :isUsed="tableUsedCache.get(getTableKey(visibleTables[virtualItem.index])) ?? false"
            />
          </li>
        </ul>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import DatabaseExplorerItems from '@/components/DatabaseExplorerItems.vue'
import { Card, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useQueryEditor } from '@/composables/useQueryEditor'
import type { Table } from '@/stores/tables'
import {
  convertCatalogAssetsToTables,
  useCatalogAssetsQuery
} from '@/components/catalog/useCatalogQuery'
import { computed, ref, watch } from 'vue'
import { useVirtualizer } from '@tanstack/vue-virtual'
import CardContent from './ui/card/CardContent.vue'

const editor = useQueryEditor()
const showTableKey = ref<string | null>(null)
const scrollElement = ref<HTMLElement | null>(null)

// Use the catalog query hook to fetch assets
const { data: catalogAssets, isLoading } = useCatalogAssetsQuery()

// Convert catalog assets to Table format
const tables = computed<Table[]>(() => {
  return convertCatalogAssetsToTables(catalogAssets.value ?? [])
})

// Debounced search input
const searchTablesInput = ref('')
let searchTimeout: ReturnType<typeof setTimeout> | null = null

function onSearchInput(event: Event) {
  const value = (event.target as HTMLInputElement).value
  if (searchTimeout) clearTimeout(searchTimeout)

  searchTimeout = setTimeout(() => {
    searchTablesInput.value = value
  }, 300) // 300ms debounce
}

function extractTables(sqlQuery: string) {
  // Regular expression to match table names following FROM, JOIN, and UPDATE keywords
  // This regex is basic and might need adjustments to cover all SQL syntax variations
  const regex = /\b(FROM|JOIN|UPDATE|INTO)\s+("?\w+"?\."?\w+"?|"\w+"|\w+)/gi

  let match
  const extables = []

  // Use a loop to find matches and push the table name to the tables array
  while ((match = regex.exec(sqlQuery)) !== null) {
    // This ensures the match was not empty or undefined
    // Note: replaceAll requires ES2021 or later
    if (match[2]) {
      // Use split/join as a fallback for replaceAll
      extables.push(match[2].split('"').join(''))
    }
  }

  return [...new Set(extables)]
}

const extractedTables = computed(() => {
  return extractTables(editor.query.sql)
})

const usedTablesMap = computed<Set<string>>(() => {
  const map = new Set<string>()
  for (const extractedTable of extractedTables.value) {
    map.add(extractedTable.toLowerCase())
  }
  return map
})

const getTableKey = (table: Table) => `${table.schema}.${table.name}`.toLowerCase()

const isTableUsed = (table: Table): boolean => {
  const key = getTableKey(table)
  return usedTablesMap.value.has(key) || usedTablesMap.value.has(table.name.toLowerCase())
}

const tableUsedCache = computed<Map<string, boolean>>(() => {
  const cache = new Map<string, boolean>()
  for (const table of tables.value) {
    cache.set(getTableKey(table), isTableUsed(table))
  }
  return cache
})

// Sort tables by used status, then filter by search
const visibleTables = computed<Table[]>(() => {
  const sortedByUsed = [...tables.value].sort((a, b) => {
    const aUsed = tableUsedCache.value.get(getTableKey(a)) ?? false
    const bUsed = tableUsedCache.value.get(getTableKey(b)) ?? false

    if (aUsed && !bUsed) return -1
    if (!aUsed && bUsed) return 1
    return 0
  })

  // Filter by search term
  const searchTerm = searchTablesInput.value.toLowerCase()
  if (!searchTerm) return sortedByUsed

  return sortedByUsed.filter(
    (table) =>
      table.name.toLowerCase().includes(searchTerm) ||
      table.schema.toLowerCase().includes(searchTerm) ||
      table.description.toLowerCase().includes(searchTerm)
  )
})

// Virtual scroller with dynamic height support
const virtualizer = useVirtualizer(
  computed(() => ({
    count: visibleTables.value.length,
    getScrollElement: () => scrollElement.value,
    estimateSize: () => 80, // Estimate: collapsed table ~80px, will be measured dynamically
    overscan: 5 // Render 5 items outside viewport
  }))
)

// Invalidate measurements when table expand/collapse state changes
watch(
  () => showTableKey.value,
  () => {
    virtualizer.value.measure()
  }
)

// Helper to measure element heights for virtualizer
function measureElement(el: any) {
  if (!el) return
  const element = el instanceof HTMLElement ? el : el?.$el
  if (element) {
    virtualizer.value.measureElement(element)
  }
}

const onClick = (key: string) => {
  if (showTableKey.value == key) {
    showTableKey.value = null
  } else {
    showTableKey.value = key
  }
}

const onSearch = (table: Table) => {
  editor.query.sql = `SELECT * FROM "${table.schema}"."${table.name}";`
  searchTablesInput.value = '' // reset input
  editor.runQuery()
}
</script>
