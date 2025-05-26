<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="py-10">
      <h1 class="text-3xl font-bold leading-tight text-gray-900">Favorites</h1>
      <p class="mt-2 text-sm text-gray-500">Your saved queries and charts</p>

      <div v-if="loading" class="mt-4 text-center">
        <p>Loading...</p>
      </div>

      <div v-else-if="error" class="mt-4 text-center text-red-500">
        <p>{{ error }}</p>
      </div>

      <div v-else>
        <!-- Saved Queries Section -->
        <div class="mt-8">
          <h2 class="text-xl font-semibold text-gray-900">Saved Queries</h2>
          <div v-if="queries.length === 0" class="mt-4 text-center text-gray-500">
            <p>No saved queries</p>
          </div>
          <div v-else class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-2">
            <div
              v-for="query in queries"
              :key="query.id"
              class="bg-white overflow-hidden shadow rounded-lg"
            >
              <div class="px-4 py-5 sm:p-6">
                <h3 class="text-lg font-medium text-gray-900 truncate">
                  {{ query.title || 'Untitled Query' }}
                </h3>
                <div class="mt-2 max-h-20 overflow-hidden text-sm text-gray-500">
                  {{ truncateSql(query.sql) }}
                </div>
                <!-- Add query result preview -->
                <div class="mt-2 border rounded p-2 bg-gray-50 overflow-auto max-h-40">
                  <div v-if="query.rows && query.rows.length > 0" class="text-xs">
                    <table class="min-w-full divide-y divide-gray-200">
                      <thead class="bg-gray-100">
                        <tr>
                          <th
                            v-for="(_, key) in query.rows[0]"
                            :key="key"
                            class="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                          >
                            {{ key }}
                          </th>
                        </tr>
                      </thead>
                      <tbody class="bg-white divide-y divide-gray-200">
                        <tr v-for="(row, i) in query.rows.slice(0, 3)" :key="i">
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
                      v-if="query.rows.length > 3"
                      class="text-center text-xs mt-1 text-gray-500"
                    >
                      + {{ query.rows.length - 3 }} more rows
                    </div>
                  </div>
                  <div v-else class="text-xs text-gray-500">No results available</div>
                </div>
                <div class="mt-4 flex justify-between">
                  <a
                    :href="`/query/${query.id}`"
                    class="text-sm font-medium text-blue-600 hover:text-blue-500"
                  >
                    View Query
                  </a>
                  <button
                    @click="unfavoriteQuery(query.id)"
                    class="text-sm text-red-600 hover:text-red-500"
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Saved Charts Section -->
        <div class="mt-8">
          <h2 class="text-xl font-semibold text-gray-900">Saved Charts</h2>
          <div v-if="charts.length === 0" class="mt-4 text-center text-gray-500">
            <p>No saved charts</p>
          </div>
          <div v-else class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-2">
            <div
              v-for="chart in charts"
              :key="chart.id"
              class="bg-white overflow-hidden shadow rounded-lg"
            >
              <div class="px-4 py-5 sm:p-6">
                <h3 class="text-lg font-medium text-gray-900 truncate">
                  {{ getChartTitle(chart) }}
                </h3>
                <div class="mt-2">
                  <Echart
                    :option="{ ...chart.config, query_id: chart.queryId }"
                    style="height: 200px; width: 100%"
                  />
                </div>
                <div class="mt-4 flex justify-between">
                  <a
                    :href="`/query/${chart.queryId}`"
                    class="text-sm font-medium text-blue-600 hover:text-blue-500"
                  >
                    View Query
                  </a>
                  <button
                    @click="unfavoriteChart(chart.id)"
                    class="text-sm text-red-600 hover:text-red-500"
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Echart from '@/components/Echart.vue'
import axios from '@/plugins/axios'
import { useChartStore } from '@/stores/chart'
import { useContextsStore } from '@/stores/contexts'
import { onMounted, ref } from 'vue'

const { toggleChartFavorite } = useChartStore()
const { contextSelected } = useContextsStore()
const queries = ref([])
const charts = ref([])
const loading = ref(true)
const error = ref(null)

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
const truncateSql = (sql) => {
  if (!sql) return ''
  return sql.length > 100 ? `${sql.substring(0, 100)}...` : sql
}

const getChartTitle = (chart) => {
  if (!chart.config) return 'Untitled Chart'
  return chart.config.title?.text || 'Untitled Chart'
}

// TODO: switch to store when Query Store is clean...
const unfavoriteQuery = async (id) => {
  try {
    await axios.post(`/api/query/${id}/favorite`)
    queries.value = queries.value.filter((q) => q.id !== id)
  } catch (err) {
    console.error('Error removing query from favorites:', err)
  }
}

const unfavoriteChart = async (id) => {
  try {
    await toggleChartFavorite(id)
    charts.value = charts.value.filter((c) => c.id !== id)
  } catch (err) {
    console.error('Error removing chart from favorites:', err)
  }
}
</script>
