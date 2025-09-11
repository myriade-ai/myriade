<template>
  <div class="overflow-y-auto h-screen bg-sidebar/50">
    <div class="px-8">
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
          <h3 class="mt-2 text-sm font-medium text-gray-900">No favorites yet</h3>
          <p class="mt-1 text-sm text-gray-500">
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
              <CardContent>
                <div class="flex items-center gap-2 mb-2">
                  <div class="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">Query</div>
                </div>
                <h3 class="text-lg font-medium text-gray-900 truncate">
                  {{ item.data.title || 'Untitled Query' }}
                </h3>
                <div
                  class="mt-2 max-h-60 overflow-hidden text-sm text-gray-500 text-ellipsis line-clamp-3"
                >
                  {{ item.data.sql }}
                </div>
                <!-- Add query result preview -->
                <div class="mt-2 border rounded p-2 bg-gray-50 overflow-auto max-h-40">
                  <div v-if="item.data.rows && item.data.rows.length > 0" class="text-xs">
                    <table class="min-w-full divide-y divide-gray-200">
                      <thead class="bg-gray-100">
                        <tr>
                          <th
                            v-for="(_, key) in item.data.rows[0]"
                            :key="key"
                            class="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                          >
                            {{ key }}
                          </th>
                        </tr>
                      </thead>
                      <tbody class="bg-white divide-y divide-gray-200">
                        <tr v-for="(row, i) in item.data.rows.slice(0, 3)" :key="i">
                          <td
                            v-for="(value, key) in row"
                            :key="key"
                            class="px-2 py-1 whitespace-nowrap text-xs text-gray-500"
                          >
                            {{ value }}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                    <div
                      v-if="item.data.rows.length > 3"
                      class="text-center text-xs mt-1 text-gray-500"
                    >
                      + {{ item.data.rows.length - 3 }} more rows
                    </div>
                  </div>
                  <div v-else class="text-xs text-gray-500">No results available</div>
                </div>
              </CardContent>

              <CardFooter class="justify-between mt-2">
                <Button
                  class="text-sm font-medium text-primary-600 hover:text-primary-500"
                  variant="link"
                  asChild
                >
                  <RouterLink :to="`/query/${item.data.id}`"> View Query </RouterLink>
                </Button>

                <Button @click="unfavoriteQuery(item.data.id)" variant="ghost_destructive">
                  Remove
                </Button>
              </CardFooter>
            </template>

            <!-- Chart Card -->
            <template v-else-if="item.type === 'chart'">
              <CardContent>
                <div class="flex items-center gap-2 mb-2">
                  <div class="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                    Chart
                  </div>
                </div>
                <h3 class="text-lg font-medium text-gray-900 truncate">
                  {{ getChartTitle(item.data) }}
                </h3>
                <div class="mt-2">
                  <Echart
                    :option="{ ...item.data.config, query_id: item.data.queryId }"
                    style="height: 200px; width: 100%"
                  />
                </div>
              </CardContent>

              <CardFooter class="justify-between">
                <Button
                  class="text-sm font-medium text-primary-600 hover:text-primary-500"
                  variant="link"
                  asChild
                >
                  <RouterLink :to="`/query/${item.data.queryId}`"> View Query </RouterLink>
                </Button>

                <Button @click="unfavoriteChart(item.data.id)" variant="ghost_destructive">
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
