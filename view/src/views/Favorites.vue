<template>
  <PageHeader title="Favorites" subtitle="Your saved queries and charts" sticky />
  <div class="flex-1 overflow-auto">
    <div class="px-6">
      <div v-if="loading" class="mt-4 text-center">
        <p>Loading...</p>
      </div>

      <div v-else-if="error" class="mt-4 text-center text-error-500">
        <p>{{ error }}</p>
      </div>

      <div v-else class="space-y-6 my-4">
        <div v-if="combinedItems.length === 0" class="text-center py-8">
          <div
            class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-primary-100"
          >
            <Heart class="h-6 w-6 text-primary-600" />
          </div>
          <h3 class="mt-2 text-sm font-medium text-foreground">No favorites yet</h3>
          <p class="mt-1 text-sm text-muted-foreground">
            Create a chat to save your favorite queries and charts for quick access later!
          </p>
          <div class="mt-6">
            <RouterLink
              to="/chat/new"
              class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 4v16m8-8H4"
                />
              </svg>
              Create your first favorite
            </RouterLink>
          </div>
        </div>

        <div
          v-if="combinedItems.length > 0"
          class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-2"
        >
          <Card
            v-for="item in combinedItems"
            :key="`${item.type}-${item.data.id}`"
            class="overflow-hidden gap-0 h-fit"
          >
            <!-- Query Card -->
            <template v-if="item.type === 'query'">
              <CardContent class="p-4 space-y-3">
                <div class="flex items-center gap-2">
                  <div
                    class="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full"
                  >
                    Query
                  </div>
                </div>
                <h3 class="text-lg font-medium text-foreground truncate">
                  {{ item.data.title || 'Untitled Query' }}
                </h3>
                <!-- Query result preview -->
                <div class="border rounded p-2 bg-muted overflow-auto max-h-48">
                  <div v-if="getTablePreview(item.data.rows)" class="text-xs">
                    <table class="min-w-full divide-y divide-gray-200">
                      <thead class="bg-muted">
                        <tr>
                          <th
                            v-for="header in getTablePreview(item.data.rows)?.headers"
                            :key="header"
                            class="px-2 py-1 text-left text-[11px] font-medium text-muted-foreground uppercase tracking-wider"
                          >
                            {{ header }}
                          </th>
                        </tr>
                      </thead>
                      <tbody class="bg-card divide-y divide-gray-200">
                        <tr v-for="(row, i) in getTablePreview(item.data.rows)?.rows" :key="i">
                          <td
                            v-for="(value, key) in row"
                            :key="key"
                            class="px-2 py-1 whitespace-nowrap text-xs text-muted-foreground"
                          >
                            {{ value }}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                    <div
                      v-if="getTablePreview(item.data.rows)?.extraCount"
                      class="text-center text-xs mt-1 text-muted-foreground"
                    >
                      + {{ getTablePreview(item.data.rows)?.extraCount }} more rows
                    </div>
                  </div>
                  <div v-else class="text-xs text-muted-foreground">No results available</div>
                </div>
              </CardContent>

              <CardFooter class="justify-end gap-2 px-4 pb-4 pt-0">
                <Button
                  class="text-sm font-medium text-primary-600 hover:text-primary-500"
                  size="sm"
                  variant="link"
                  asChild
                >
                  <RouterLink :to="`/query/${item.data.id}`"> View Query </RouterLink>
                </Button>

                <Button
                  size="sm"
                  @click="unfavoriteQuery(item.data.id)"
                  variant="ghost_destructive"
                  class="px-3"
                >
                  Remove
                </Button>
              </CardFooter>
            </template>

            <!-- Chart Card -->
            <template v-else-if="item.type === 'chart'">
              <CardContent class="p-4 space-y-3">
                <div class="flex items-center gap-2">
                  <div
                    class="px-2 py-1 text-xs bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded-full"
                  >
                    Chart
                  </div>
                </div>
                <h3 class="text-lg font-medium text-foreground truncate">
                  {{ getChartTitle(item.data) }}
                </h3>
                <div class="rounded border bg-muted p-2">
                  <Echart
                    :option="{ ...item.data.config, query_id: item.data.queryId }"
                    style="height: 200px; width: 100%"
                  />
                </div>

                <div class="border rounded p-2 bg-muted overflow-auto max-h-48">
                  <div v-if="getChartTablePreview(item.data)" class="text-xs">
                    <table class="min-w-full divide-y divide-gray-200">
                      <thead class="bg-muted">
                        <tr>
                          <th
                            v-for="header in getChartTablePreview(item.data)?.headers"
                            :key="header"
                            class="px-2 py-1 text-left text-[11px] font-medium text-muted-foreground uppercase tracking-wider"
                          >
                            {{ header }}
                          </th>
                        </tr>
                      </thead>
                      <tbody class="bg-card divide-y divide-gray-200">
                        <tr v-for="(row, i) in getChartTablePreview(item.data)?.rows" :key="i">
                          <td
                            v-for="(value, key) in row"
                            :key="key"
                            class="px-2 py-1 whitespace-nowrap text-xs text-muted-foreground"
                          >
                            {{ value }}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                    <div
                      v-if="getChartTablePreview(item.data)?.extraCount"
                      class="text-center text-xs mt-1 text-muted-foreground"
                    >
                      + {{ getChartTablePreview(item.data)?.extraCount }} more rows
                    </div>
                  </div>
                  <div v-else class="text-xs text-muted-foreground">No data available</div>
                </div>
              </CardContent>

              <CardFooter class="justify-end gap-2 px-4 pb-4 pt-0">
                <Button
                  class="text-sm font-medium text-primary-600 hover:text-primary-500"
                  size="sm"
                  variant="link"
                  asChild
                >
                  <RouterLink :to="`/query/${item.data.queryId}`"> View Query </RouterLink>
                </Button>

                <Button
                  size="sm"
                  @click="unfavoriteChart(item.data.id)"
                  variant="ghost_destructive"
                  class="px-3"
                >
                  Remove
                </Button>
              </CardFooter>
            </template>
          </Card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Echart from '@/components/Echart.vue'
import PageHeader from '@/components/PageHeader.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import type { Query } from '@/composables/useQueryEditor'
import axios from '@/plugins/axios'
import { useChartStore, type Chart } from '@/stores/chart'
import { useContextsStore } from '@/stores/contexts'
import { Heart } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

const { toggleChartFavorite } = useChartStore()
const { contextSelected } = useContextsStore()

const queries = ref<Query[]>([])

const charts = ref<Chart[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

// Combined items for mixed display
const combinedItems = computed(() => {
  const queryItems = queries.value.map((query) => ({
    type: 'query' as const,
    data: query,
    id: `query-${query.id}`
  }))

  const chartItems = charts.value.map((chart) => ({
    type: 'chart' as const,
    data: chart,
    id: `chart-${chart.id}`
  }))

  return [...queryItems, ...chartItems]
})

// Fetch workspace items on mount
onMounted(async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/favorites?contextId=' + contextSelected?.id)
    queries.value = response.data.queries
    charts.value = response.data.charts
  } catch (err) {
    console.error('Error fetching workspace items:', err)
    error.value = 'Failed to load workspace items'
  } finally {
    loading.value = false
  }
})

// Helper functions
const getChartTitle = (chart: Chart) => {
  if (!chart.config) return 'Untitled Chart'
  return chart.config.title?.text || 'Untitled Chart'
}

const getTablePreview = (rows?: Record<string, any>[]) => {
  if (!rows || rows.length === 0) return null

  const headers = Object.keys(rows[0])
  const previewRows = rows.slice(0, 3)
  const extraCount = rows.length - previewRows.length

  if (headers.length === 0) return null

  return {
    headers,
    rows: previewRows,
    extraCount: extraCount > 0 ? extraCount : 0
  }
}

const getChartTablePreview = (chart: Chart) => {
  const source = chart.config?.dataset?.source

  if (!Array.isArray(source) || source.length === 0) return null

  let headers: string[] = []
  let dataRows: Record<string, any>[] = []

  if (Array.isArray(source[0])) {
    const [headerRow, ...rest] = source as any[][]
    if (!Array.isArray(headerRow)) return null
    headers = headerRow.map(String)
    dataRows = rest.map((row) =>
      Object.fromEntries(headers.map((header, index) => [header, Array.isArray(row) ? row[index] : undefined]))
    )
  } else if (typeof source[0] === 'object' && source[0] !== null) {
    headers = Object.keys(source[0] as Record<string, any>)
    dataRows = source as Record<string, any>[]
  }

  if (headers.length === 0 || dataRows.length === 0) return null

  const previewRows = dataRows.slice(0, 3)
  const extraCount = Math.max(0, dataRows.length - previewRows.length)

  return {
    headers,
    rows: previewRows,
    extraCount
  }
}

// TODO: switch to store when Query Store is clean...
const unfavoriteQuery = async (id: string | number) => {
  try {
    await axios.post(`/api/query/${id}/favorite`)
    queries.value = queries.value.filter((q) => q.id !== id)
  } catch (err) {
    console.error('Error removing query from favorites:', err)
  }
}

const unfavoriteChart = async (id: string | number) => {
  try {
    await toggleChartFavorite(String(id))
    charts.value = charts.value.filter((c) => c.id !== id)
  } catch (err) {
    console.error('Error removing chart from favorites:', err)
  }
}
</script>
