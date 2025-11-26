<template>
  <div
    class="flex-1 overflow-y-auto bg-gradient-to-b from-card to-muted/20 dark:from-background dark:to-muted/10"
  >
    <CatalogDetailsHeader
      v-if="asset"
      :asset="asset"
      :asset-icon="assetIcon"
      :asset-label="assetLabel"
      :table-summary="tableSummary"
      :columns-count="columns.length"
      @publish="$emit('publish')"
    />

    <Tabs v-model="activeTabModel" class="flex flex-1 flex-col min-h-0">
      <TabsList
        class="flex w-full flex-wrap gap-2 border-b border-border bg-gradient-to-r from-muted/60 via-muted/40 to-muted/60 dark:from-muted/30 dark:via-muted/20 dark:to-muted/30 flex-shrink-0 rounded-none px-2"
      >
        <TabsTrigger value="overview">
          <FileText class="h-4 w-4 md:hidden" />
          <span class="hidden md:inline">Overview</span>
        </TabsTrigger>
        <TabsTrigger v-if="isDatabaseAsset" value="schemas">
          <FolderTree class="h-4 w-4 md:hidden" />
          <span class="hidden md:inline">Schemas</span>
        </TabsTrigger>
        <TabsTrigger v-if="isSchemaAsset" value="tables">
          <TableIcon class="h-4 w-4 md:hidden" />
          <span class="hidden md:inline">Tables</span>
        </TabsTrigger>
        <TabsTrigger v-if="isTableAsset" value="columns">
          <Columns3 class="h-4 w-4 md:hidden" />
          <span class="hidden md:inline">Columns</span>
        </TabsTrigger>
        <TabsTrigger v-if="isTableAsset" value="preview">
          <Eye class="h-4 w-4 md:hidden" />
          <span class="hidden md:inline">Preview</span>
        </TabsTrigger>
        <TabsTrigger value="sources">
          <Link2 class="h-4 w-4 md:hidden" />
          <span class="hidden md:inline">Sources</span>
        </TabsTrigger>
      </TabsList>
      <div class="flex-1 overflow-y-auto">
        <TabsContent value="overview" class="space-y-4 p-2">
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
            @approve-description="$emit('approve-description', $event)"
            @approve-tags="$emit('approve-tags', $event)"
            @reject-description="$emit('reject-description')"
            @reject-tags="$emit('reject-tags')"
          />

          <!-- Activity Feed -->
          <AssetFeed v-if="asset" :asset-id="asset.id" />
        </TabsContent>

        <TabsContent v-if="isDatabaseAsset" value="schemas" class="space-y-4">
          <CatalogSchemasTab
            :schemas="schemas"
            :selected-asset-id="asset?.id ?? null"
            @select-schema="handleSelectSchema"
          />
        </TabsContent>

        <TabsContent v-if="isSchemaAsset" value="tables" class="space-y-4">
          <CatalogTablesTab
            :tables="tables"
            :selected-asset-id="asset?.id ?? null"
            @select-table="handleSelectTable"
          />
        </TabsContent>

        <TabsContent v-if="isTableAsset" value="columns" class="space-y-4">
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
import AssetFeed from '@/components/catalog/AssetFeed.vue'
import AssetPreviewTab from '@/components/catalog/AssetPreviewTab.vue'
import AssetSourcesTab from '@/components/catalog/AssetSourcesTab.vue'
import CatalogColumnsTab from '@/components/catalog/CatalogColumnsTab.vue'
import CatalogSchemasTab from '@/components/catalog/CatalogSchemasTab.vue'
import CatalogTablesTab from '@/components/catalog/CatalogTablesTab.vue'
import CatalogDetailsHeader from '@/components/catalog/CatalogDetailsHeader.vue'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { CatalogAsset } from '@/stores/catalog'
import {
  CircleQuestionMarkIcon,
  Columns3,
  Database,
  FileText,
  Eye,
  FolderTree,
  Link2,
  Table as TableIcon,
  View as ViewIcon
} from 'lucide-vue-next'
import { computed } from 'vue'
import type {
  EditableDraft,
  ExplorerColumnNode,
  ExplorerSchemaNode,
  ExplorerTableNode
} from './types'

interface Props {
  asset: CatalogAsset | null
  columns: ExplorerColumnNode[]
  schemas: ExplorerSchemaNode[]
  tables: ExplorerTableNode[]
  activeTab: 'overview' | 'columns' | 'schemas' | 'tables' | 'preview' | 'sources'
  draft: EditableDraft
  isEditing: boolean
  isSaving: boolean
  hasChanges: boolean
  error: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:activeTab': [value: 'overview' | 'columns' | 'schemas' | 'tables' | 'preview' | 'sources']
  'select-column': [columnId: string]
  'select-schema': [schemaId: string]
  'select-table': [tableId: string]
  'start-edit': []
  'cancel-edit': []
  save: []
  publish: []
  'update:draft': [draft: EditableDraft]
  'dismiss-flag': []
  'approve-description': [description: string]
  'approve-tags': [tagIds: string[]]
  'reject-description': []
  'reject-tags': []
}>()

// Computed properties that were previously passed as props
const isTableAsset = computed(() => {
  return props.asset?.type === 'TABLE'
})

const isDatabaseAsset = computed(() => {
  return props.asset?.type === 'DATABASE'
})

const isSchemaAsset = computed(() => {
  return props.asset?.type === 'SCHEMA'
})

const getAssetIcon = (asset: CatalogAsset | null) => {
  if (!asset) return CircleQuestionMarkIcon
  if (asset.type === 'DATABASE') {
    return Database
  }
  if (asset.type === 'SCHEMA') {
    return FolderTree
  }
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
  if (asset.type === 'DATABASE') {
    return asset.database_facet?.database_name || asset.name || 'Unnamed database'
  }
  if (asset.type === 'SCHEMA') {
    return asset.schema_facet?.schema_name || asset.name || 'default'
  }
  if (asset.type === 'TABLE') {
    return asset.table_facet?.table_name || asset.name || 'Unnamed table'
  }
  return asset.column_facet?.column_name || asset.name || 'Unnamed column'
})

const tableSummary = computed(() => {
  const asset = props.asset
  if (!asset) return ''

  // For databases
  if (asset.type === 'DATABASE' && asset.database_facet) {
    return asset.database_facet.database_name || ''
  }

  // For schemas
  if (asset.type === 'SCHEMA' && asset.schema_facet) {
    const dbName = asset.schema_facet.database_name || ''
    const schemaName = asset.schema_facet.schema_name || 'default'
    return `${dbName}.${schemaName}`
  }

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

function handleSelectSchema(schemaId: string) {
  emit('select-schema', schemaId)
  emit('update:activeTab', 'overview')
}

function handleSelectTable(tableId: string) {
  emit('select-table', tableId)
  emit('update:activeTab', 'overview')
}
</script>
