<template>
  <div class="overflow-hidden">
    <!-- Database Header -->
    <div class="px-6 py-4 bg-white">
      <!-- First row: Database name, progress bar, percentage -->
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-3">
          <Database class="h-5 w-5 text-slate-600" />
          <h3 class="font-semibold text-sm text-slate-900">{{ database.database_name }}</h3>
        </div>
        <ProgressBar :percentage="database.completion_percentage" size="sm" />
      </div>

      <!-- Second row: Metadata -->
      <div class="flex items-center justify-between text-xs text-slate-500">
        <span
          >{{ database.total_schemas }} schemas • {{ database.total_tables }} tables •
          {{ database.total_columns.toLocaleString() }} columns</span
        >
      </div>
    </div>

    <!-- Schemas Section -->
    <div v-if="database.schemas.length > 0">
      <!-- Schemas Toggle Button -->
      <button
        class="w-full px-6 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors border-t border-slate-200 text-left bg-slate-100"
        @click="isExpanded = !isExpanded"
      >
        <span
          class="text-xs font-semibold text-slate-700 uppercase tracking-wide flex items-center gap-2"
        >
          <ChevronRight v-if="!isExpanded" class="h-4 w-4 text-slate-500" />
          <ChevronDown v-else class="h-4 w-4 text-slate-500" />
          Schemas:
        </span>
      </button>

      <!-- Schemas List -->
      <div v-show="isExpanded" class="divide-y divide-slate-200 bg-slate-50/50">
        <div
          v-for="schema in sortedSchemas"
          :key="schema.schema_name"
          class="px-6 py-3 hover:bg-slate-100 transition-colors flex items-center justify-between gap-4"
        >
          <div class="flex items-center gap-3 flex-1 min-w-0">
            <FolderTree class="h-4 w-4 text-slate-500 flex-shrink-0" />
            <span class="text-sm font-medium text-slate-900 truncate">{{
              schema.schema_name
            }}</span>
            <ProgressBar :percentage="schema.completion_percentage" size="sm" />
            <span class="text-sm text-slate-500 flex-shrink-0"
              >{{ schema.table_count }} tables</span
            >
          </div>
          <button
            @click.stop="navigateToSchema(schema.schema_asset_id)"
            class="text-xs text-blue-600 hover:text-blue-700 font-medium flex-shrink-0 whitespace-nowrap"
          >
            View →
          </button>
        </div>
      </div>

      <!-- Collapse Button -->
      <button
        v-show="isExpanded"
        @click="isExpanded = false"
        class="w-full px-6 py-2 text-xs font-semibold text-slate-700 uppercase tracking-wide hover:bg-slate-50 transition-colors border-t border-slate-200"
      >
        <ChevronUp class="h-4 w-4 text-slate-500 inline mr-2" />
        Collapse schemas
      </button>
    </div>

    <!-- Empty State -->
    <div v-else class="px-6 py-3 text-center bg-slate-50">
      <p class="text-xs text-slate-500">No schemas found</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import ProgressBar from './ProgressBar.vue'
import { ChevronDown, ChevronUp, ChevronRight, Database, FolderTree } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { DatabaseStats } from '@/composables/useDashboardStats'

interface Props {
  database: DatabaseStats
}

const props = defineProps<Props>()
const router = useRouter()

const isExpanded = ref(false)

const sortedSchemas = computed(() => {
  return [...(props.database?.schemas || [])].sort((a, b) =>
    a.schema_name.localeCompare(b.schema_name)
  )
})

const navigateToSchema = (schemaAssetId: string) => {
  router.push({
    name: 'AssetPage',
    query: {
      assetId: schemaAssetId
    }
  })
}
</script>
