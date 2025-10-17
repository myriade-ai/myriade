<template>
  <div class="px-2 py-2 h-full flex flex-col min-h-0">
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-8">
      <LoaderIcon class="mr-2" />
      <span class="text-sm text-slate-600">Loading preview...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-red-600 mb-4">{{ error }}</p>
      <Button @click="fetchPreview" variant="outline" size="sm">Retry</Button>
    </div>

    <!-- Preview Data -->
    <div
      v-else-if="previewData && previewData.rows.length > 0"
      class="flex flex-col gap-3 flex-1 min-h-0"
    >
      <div class="text-sm text-slate-600">
        Showing {{ previewData.count }} random row{{ previewData.count !== 1 ? 's' : '' }}
      </div>

      <div class="overflow-auto flex-1 rounded-md border border-slate-200">
        <table class="w-full text-sm">
          <thead class="bg-slate-50 sticky top-0">
            <tr>
              <th
                v-for="column in columns"
                :key="column"
                class="px-4 py-2 text-left font-medium text-slate-700 border-b border-slate-200"
              >
                {{ column }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, rowIndex) in previewData.rows"
              :key="rowIndex"
              class="border-b border-slate-100 hover:bg-slate-50"
            >
              <td
                v-for="column in columns"
                :key="column"
                class="px-4 py-2 text-slate-600 max-w-xs truncate"
                :title="formatCellValue(row[column])"
              >
                {{ formatCellValue(row[column]) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-8 text-slate-600">
      <p>No data available for preview</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import axios from '@/plugins/axios'
import type { CatalogAsset } from '@/stores/catalog'
import LoaderIcon from '@/components/icons/LoaderIcon.vue'
import { Button } from '@/components/ui/button'

interface Props {
  asset: CatalogAsset | null
}

const props = defineProps<Props>()

interface PreviewData {
  rows: Record<string, any>[]
  count: number
}

const previewData = ref<PreviewData | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const columns = computed(() => {
  if (!previewData.value || previewData.value.rows.length === 0) {
    return []
  }
  return Object.keys(previewData.value.rows[0])
})

async function fetchPreview() {
  if (!props.asset || props.asset.type !== 'TABLE') {
    return
  }

  loading.value = true
  error.value = null
  previewData.value = null

  try {
    const response = await axios.get(`/api/catalogs/assets/${props.asset.id}/preview`, {
      params: { limit: 10 }
    })
    previewData.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to fetch preview data'
    console.error('Error fetching preview:', err)
  } finally {
    loading.value = false
  }
}

function formatCellValue(value: any): string {
  if (value === null || value === undefined) {
    return 'NULL'
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

// Fetch preview when component is mounted or asset changes
watch(
  () => props.asset?.id,
  () => {
    fetchPreview()
  },
  { immediate: true }
)
</script>
