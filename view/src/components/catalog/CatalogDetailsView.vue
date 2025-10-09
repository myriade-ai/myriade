<template>
  <div class="flex-1 overflow-y-auto bg-gradient-to-b from-white to-slate-50/30">
    <CatalogDetailsHeader
      v-if="asset"
      :asset="asset"
      :asset-icon="assetIcon"
      :asset-label="assetLabel"
      :table-summary="tableSummary"
      :columns-count="columns.length"
    />

    <Tabs v-model="activeTabModel" class="flex flex-1 flex-col min-h-0">
      <TabsList
        class="flex w-full flex-wrap gap-2 border-b border-slate-200 bg-gradient-to-r from-slate-100/80 via-stone-100/80 to-slate-100/80 flex-shrink-0 rounded-none px-2"
      >
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="columns">Columns</TabsTrigger>
      </TabsList>
      <div class="flex-1 overflow-y-auto">
        <TabsContent value="overview" class="space-y-4 px-4 py-2">
          <!-- Column Overview -->
          <CatalogColumnOverview
            v-if="asset?.type === 'COLUMN'"
            :asset="asset"
            :draft="draft"
            :is-editing="isEditing"
            :is-saving="isSaving"
            :has-changes="hasChanges"
            :error="error"
            @start-edit="$emit('start-edit')"
            @cancel-edit="$emit('cancel-edit')"
            @save="$emit('save')"
            @update:draft="$emit('update:draft', $event)"
          />

          <!-- Table/Asset Overview -->
          <CatalogTableOverview
            v-else-if="asset"
            :asset="asset"
            :draft="draft"
            :is-editing="isEditing"
            :is-saving="isSaving"
            :has-changes="hasChanges"
            :error="error"
            :columns-count="columns.length"
            @start-edit="$emit('start-edit')"
            @cancel-edit="$emit('cancel-edit')"
            @save="$emit('save')"
            @update:draft="$emit('update:draft', $event)"
          />
        </TabsContent>

        <TabsContent value="columns" class="space-y-4">
          <CatalogColumnsTab
            :columns="columns"
            :selected-asset-id="asset?.id ?? null"
            @select-column="handleSelectColumn"
          />
        </TabsContent>
      </div>
    </Tabs>
  </div>
</template>

<script setup lang="ts">
import CatalogColumnsTab from '@/components/catalog/CatalogColumnsTab.vue'
import CatalogColumnOverview from '@/components/catalog/CatalogColumnOverview.vue'
import CatalogDetailsHeader from '@/components/catalog/CatalogDetailsHeader.vue'
import CatalogTableOverview from '@/components/catalog/CatalogTableOverview.vue'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { computed } from 'vue'
import type { CatalogAsset } from '@/stores/catalog'
import { Columns3, Table as TableIcon } from 'lucide-vue-next'
import type { EditableDraft, ExplorerColumnNode } from './types'

interface Props {
  asset: CatalogAsset | null
  columns: ExplorerColumnNode[]
  activeTab: 'overview' | 'columns'
  draft: EditableDraft
  isEditing: boolean
  isSaving: boolean
  hasChanges: boolean
  error: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:activeTab': [value: 'overview' | 'columns']
  'select-column': [columnId: string]
  'start-edit': []
  'cancel-edit': []
  save: []
  'update:draft': [draft: EditableDraft]
}>()

// Computed properties that were previously passed as props
const assetIcon = computed(() => {
  if (!props.asset) return TableIcon
  return props.asset.type === 'TABLE' ? TableIcon : Columns3
})

const assetLabel = computed(() => {
  const asset = props.asset
  if (!asset) return ''
  if (asset.type === 'TABLE') {
    return asset.table_facet?.table_name || 'Unnamed table'
  }
  return asset.column_facet?.column_name || 'Unnamed column'
})

const tableSummary = computed(() => {
  const asset = props.asset
  if (!asset) return ''

  // For columns, get the parent table info from the parent_table_facet
  if (asset.type === 'COLUMN' && asset.column_facet?.parent_table_facet) {
    const schema = asset.column_facet.parent_table_facet.schema || 'default'
    const tableName = asset.column_facet.parent_table_facet.table_name || 'table'
    return `${schema}.${tableName}`
  }

  // For tables
  if (asset.type === 'TABLE' && asset.table_facet) {
    const schema = asset.table_facet.schema || 'default'
    const tableName = asset.table_facet.table_name || asset.name
    return `${schema}.${tableName}`
  }

  return ''
})

const activeTabModel = computed({
  get: () => props.activeTab,
  set: (value) => emit('update:activeTab', value)
})

function handleSelectColumn(columnId: string) {
  emit('select-column', columnId)
  emit('update:activeTab', 'overview')
}
</script>
