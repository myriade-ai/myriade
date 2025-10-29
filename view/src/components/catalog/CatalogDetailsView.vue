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
        <TabsTrigger v-if="isTableAsset" value="preview">Preview</TabsTrigger>
        <TabsTrigger value="sources">Sources</TabsTrigger>
      </TabsList>
      <div class="flex-1 overflow-y-auto">
        <TabsContent value="overview" class="space-y-4 px-2 py-2">
          <!-- Asset Overview (works for both tables and columns) -->
          <AssetDescriptionEditor
            v-if="asset"
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
            @dismiss-flag="$emit('dismiss-flag')"
            @approve-suggestion="$emit('approve-suggestion', $event)"
          />
        </TabsContent>

        <TabsContent value="columns" class="space-y-4">
          <CatalogColumnsTab
            :columns="columns"
            :selected-asset-id="asset?.id ?? null"
            @select-column="handleSelectColumn"
          />
        </TabsContent>

        <TabsContent v-if="isTableAsset" value="preview" class="space-y-4">
          <AssetPreviewTab :asset="asset" />
        </TabsContent>

        <TabsContent value="sources" class="space-y-4">
          <AssetSourcesTab :asset-id="asset?.id ?? null" />
        </TabsContent>
      </div>
    </Tabs>
  </div>
</template>

<script setup lang="ts">
import AssetDescriptionEditor from '@/components/catalog/AssetDescriptionEditor.vue'
import AssetPreviewTab from '@/components/catalog/AssetPreviewTab.vue'
import AssetSourcesTab from '@/components/catalog/AssetSourcesTab.vue'
import CatalogColumnsTab from '@/components/catalog/CatalogColumnsTab.vue'
import CatalogDetailsHeader from '@/components/catalog/CatalogDetailsHeader.vue'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { CatalogAsset } from '@/stores/catalog'
import {
  CircleQuestionMarkIcon,
  Columns3,
  Table as TableIcon,
  View as ViewIcon
} from 'lucide-vue-next'
import { computed } from 'vue'
import type { EditableDraft, ExplorerColumnNode } from './types'

interface Props {
  asset: CatalogAsset | null
  columns: ExplorerColumnNode[]
  activeTab: 'overview' | 'columns' | 'preview' | 'sources'
  draft: EditableDraft
  isEditing: boolean
  isSaving: boolean
  hasChanges: boolean
  error: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:activeTab': [value: 'overview' | 'columns' | 'preview' | 'sources']
  'select-column': [columnId: string]
  'start-edit': []
  'cancel-edit': []
  save: []
  'update:draft': [draft: EditableDraft]
  'dismiss-flag': []
  'approve-suggestion': [payload: { description: string; tagIds: string[] }]
}>()

// Computed properties that were previously passed as props
const isTableAsset = computed(() => {
  return props.asset?.type === 'TABLE'
})

const getAssetIcon = (asset: CatalogAsset | null) => {
  if (!asset) return CircleQuestionMarkIcon
  if (asset.type === 'TABLE') {
    if (asset.table_facet?.table_type === 'VIEW') {
      return ViewIcon
    }
    return TableIcon
  }
  if (asset.type === 'COLUMN') {
    return Columns3
  }
  return CircleQuestionMarkIcon
}

const assetIcon = computed(() => getAssetIcon(props.asset))

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
