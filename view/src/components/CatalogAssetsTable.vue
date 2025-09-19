<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center space-x-4">
        <h3 class="text-lg font-medium text-gray-900">Assets Overview</h3>
      </div>
      <div class="flex items-center space-x-2">
        <Input
          v-model="searchQuery"
          placeholder="Search assets..."
          class="w-64"
          @input="onSearch"
        />
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-8">
      <LoaderIcon />
      <span class="ml-2">Loading assets...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-red-600 mb-4">{{ error }}</p>
      <Button @click="refresh" variant="outline">Retry</Button>
    </div>

    <!-- Assets Table -->
    <div v-else class="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div v-if="filteredData.length === 0" class="p-8 text-center text-gray-500">
        <p>No assets found</p>
        <p class="text-sm mt-1">Try adjusting your search or filters</p>
      </div>

      <div v-else>
        <Table class="table-fixed">
          <TableHeader>
            <TableRow
              v-for="headerGroup in table.getHeaderGroups()"
              :key="headerGroup.id"
              class="border-b border-gray-200"
            >
              <TableHead
                v-for="header in headerGroup.headers"
                :key="header.id"
                :style="{ width: `${header.getSize()}px` }"
                class="text-left"
              >
                <FlexRender
                  v-if="!header.isPlaceholder"
                  :render="header.column.columnDef.header"
                  :props="header.getContext()"
                />
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <template v-if="table.getRowModel().rows?.length">
              <TableRow
                v-for="row in table.getRowModel().rows"
                :key="row.id"
                :class="getRowClass(row.original)"
                @click="() => row.getCanExpand() && row.toggleExpanded()"
                :style="{ cursor: row.getCanExpand() ? 'pointer' : 'default' }"
              >
                <TableCell
                  v-for="cell in row.getVisibleCells()"
                  :key="cell.id"
                  :style="{ width: `${cell.column.getSize()}px` }"
                  class="py-2"
                >
                  <FlexRender :render="cell.column.columnDef.cell" :props="cell.getContext()" />
                </TableCell>
              </TableRow>
            </template>
            <template v-else>
              <TableRow>
                <TableCell :colSpan="columns.length" class="h-24 text-center">
                  No results.
                </TableCell>
              </TableRow>
            </template>
          </TableBody>
        </Table>
      </div>
    </div>

    <!-- Stats Summary -->
    <div v-if="!loading && !error" class="mt-4 text-sm text-gray-600">
      <div class="flex justify-between">
        <span>
          Showing {{ totalVisibleTables }} tables and {{ totalVisibleColumns }} columns
          {{ searchQuery ? `matching "${searchQuery}"` : '' }}
        </span>
        <span> {{ totalSchemas }} schemas </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import LoaderIcon from '@/components/icons/LoaderIcon.vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table'
import { useCatalogStore, type CatalogAsset } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'
import {
  FlexRender,
  getCoreRowModel,
  getExpandedRowModel,
  getFilteredRowModel,
  useVueTable,
  type ColumnDef,
  type ExpandedState
} from '@tanstack/vue-table'
import { Sparkles } from 'lucide-vue-next'
import { computed, h, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

interface CatalogTableRow {
  id: string
  type: 'schema' | 'table' | 'column'
  name: string
  description?: string
  dataType?: string
  privacy?: boolean
  tags?: string[]
  columnCount?: number
  tableCount?: number
  asset?: CatalogAsset
  canExpand: boolean
  children?: CatalogTableRow[]
}

interface TableWithColumns {
  asset: CatalogAsset
  columns: CatalogAsset[]
}

interface SchemaGroup {
  name: string
  tables: TableWithColumns[]
  totalColumns: number
}

const catalogStore = useCatalogStore()
const contextsStore = useContextsStore()
const router = useRouter()

const searchQuery = ref('')
const expanded = ref<ExpandedState>({})
const searchTimeout = ref<ReturnType<typeof setTimeout> | null>(null)

const loading = computed(() => catalogStore.loading)
const error = computed(() => catalogStore.error)

const columns: ColumnDef<CatalogTableRow>[] = [
  {
    id: 'name',
    header: 'Name',
    size: 400,
    minSize: 300,
    maxSize: 500,
    cell: ({ row, getValue }) => {
      const rowData = row.original
      const name = getValue() as string
      const canExpand = row.getCanExpand()

      return h(
        'div',
        {
          class: `flex items-center space-x-2`,
          style: { paddingLeft: `${row.depth * 20}px` }
        },
        [
          canExpand
            ? h(
                'button',
                {
                  onClick: (e: Event) => {
                    e.stopPropagation()
                    row.toggleExpanded()
                  },
                  class: 'flex items-center justify-center w-4 h-4'
                },
                [
                  h(row.getIsExpanded() ? ChevronDownIcon : ChevronRightIcon, {
                    class: 'h-3 w-3 text-gray-500'
                  })
                ]
              )
            : h('div', { class: 'w-4' }),
          h('div', { class: 'flex items-center space-x-2' }, [
            h(
              'span',
              {
                class:
                  rowData.type === 'schema'
                    ? 'font-medium text-gray-900'
                    : rowData.type === 'table'
                      ? 'font-medium text-blue-600 hover:text-blue-800 cursor-pointer'
                      : 'font-medium text-gray-900'
              },
              name
            ),
            h(
              'span',
              {
                class: `inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  rowData.type === 'schema'
                    ? 'bg-gray-100 text-gray-800'
                    : rowData.type === 'table'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-green-100 text-green-800'
                }`
              },
              rowData.type.toUpperCase()
            )
          ])
        ]
      )
    },
    accessorFn: (row) => {
      if (row.type === 'schema') {
        return row.name || 'Default Schema'
      }
      if (row.type === 'table') {
        return row.asset?.name || row.asset?.table_facet?.table_name || 'Unnamed Table'
      }
      return row.asset?.column_facet?.column_name || 'Unnamed Column'
    }
  },
  {
    id: 'type',
    header: 'Type',
    size: 120,
    minSize: 120,
    maxSize: 150,
    accessorFn: (row) => row.dataType || '',
    cell: ({ getValue, row }) => {
      const value = getValue() as string
      const rowData = row.original

      if (rowData.type === 'column' && value) {
        return h(
          'span',
          {
            class: 'text-sm text-gray-600 font-mono'
          },
          value
        )
      }
      return ''
    }
  },
  {
    id: 'description',
    header: 'Description',
    size: 300,
    minSize: 200,
    accessorFn: (row) => row.description || '',
    cell: ({ getValue, row }) => {
      const value = getValue() as string
      const rowData = row.original

      if (value) {
        return h(
          'div',
          {
            class: 'text-sm text-gray-600 truncate overflow-hidden',
            title: value
          },
          value
        )
      }

      if (rowData.type === 'schema' && rowData.tableCount && rowData.columnCount) {
        return h(
          'span',
          {
            class: 'text-sm text-gray-500'
          },
          `${rowData.tableCount} tables, ${rowData.columnCount} columns`
        )
      }

      if (rowData.type === 'table' && rowData.columnCount) {
        return h(
          'span',
          {
            class: 'text-sm text-gray-500'
          },
          `${rowData.columnCount} columns`
        )
      }

      return h(
        'div',
        {
          class: 'flex items-center space-x-2'
        },
        [
          h(
            'span',
            {
              class: 'text-sm text-gray-500'
            },
            'No description'
          ),
          h(
            'button',
            {
              onClick: (e: Event) => {
                e.stopPropagation()
                fillDescription(rowData)
              },
              class:
                'inline-flex items-center justify-center w-4 h-4 p-0 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors',
              title: 'Fill description with AI'
            },
            [
              h(Sparkles, {
                class: 'h-3 w-3 text-primary-600'
              })
            ]
          )
        ]
      )
    }
  }
]

const groupedAssets = computed(() => {
  const assets = catalogStore.assetsArray
  const schemas: Record<string, SchemaGroup> = {}

  const tableAssets = assets.filter((asset) => asset.type === 'TABLE')
  const columnAssets = assets.filter((asset) => asset.type === 'COLUMN')

  tableAssets.forEach((table) => {
    const schemaName = table.table_facet?.schema || ''

    if (!schemas[schemaName]) {
      schemas[schemaName] = {
        name: schemaName,
        tables: [],
        totalColumns: 0
      }
    }

    const tableColumns = columnAssets.filter(
      (column) => column.column_facet?.parent_table_asset_id === table.id
    )

    schemas[schemaName].tables.push({
      asset: table,
      columns: tableColumns.sort(
        (a, b) => (a.column_facet?.ordinal || 0) - (b.column_facet?.ordinal || 0)
      )
    })

    schemas[schemaName].totalColumns += tableColumns.length
  })

  Object.values(schemas).forEach((schema) => {
    schema.tables.sort((a, b) => {
      const nameA = a.asset.name || a.asset.table_facet?.table_name || ''
      const nameB = b.asset.name || b.asset.table_facet?.table_name || ''
      return nameA.localeCompare(nameB)
    })
  })

  return Object.values(schemas).sort((a, b) => a.name.localeCompare(b.name))
})

const tableData = computed(() => {
  const rows: CatalogTableRow[] = []

  groupedAssets.value.forEach((schema) => {
    const tableRows: CatalogTableRow[] = schema.tables.map((table) => {
      const columnRows: CatalogTableRow[] = table.columns.map((column) => ({
        id: `column-${column.id}`,
        type: 'column',
        name: column.column_facet?.column_name || 'Unnamed Column',
        description: column.description || undefined,
        dataType: column.column_facet?.data_type || undefined,
        privacy: !!column.column_facet?.privacy,
        tags: column.tags || undefined,
        asset: column,
        canExpand: false
      }))

      return {
        id: `table-${table.asset.id}`,
        type: 'table',
        name: table.asset.name || table.asset.table_facet?.table_name || 'Unnamed Table',
        description: table.asset.description || undefined,
        columnCount: table.columns.length,
        asset: table.asset,
        canExpand: table.columns.length > 0,
        children: columnRows.length > 0 ? columnRows : undefined
      }
    })

    rows.push({
      id: `schema-${schema.name}`,
      type: 'schema',
      name: schema.name || 'Default Schema',
      tableCount: schema.tables.length,
      columnCount: schema.totalColumns,
      canExpand: schema.tables.length > 0,
      children: tableRows.length > 0 ? tableRows : undefined
    })
  })

  return rows
})

const filteredData = computed(() => {
  let data = tableData.value

  const filterHierarchy = (rows: CatalogTableRow[], searchQuery: string): CatalogTableRow[] => {
    return rows
      .map((row) => {
        const filteredChildren = row.children ? filterHierarchy(row.children, searchQuery) : []

        const matchesSearch =
          !searchQuery ||
          row.name.toLowerCase().includes(searchQuery) ||
          (row.description || '').toLowerCase().includes(searchQuery) ||
          (row.dataType || '').toLowerCase().includes(searchQuery) ||
          (row.tags || []).join(' ').toLowerCase().includes(searchQuery)

        // Include row if:
        // 1. Row matches search AND (has no children OR has filtered children)
        // 2. OR row has children that match (even if parent doesn't match)
        const shouldInclude = matchesSearch || filteredChildren.length > 0

        if (shouldInclude) {
          return {
            ...row,
            children: filteredChildren.length > 0 ? filteredChildren : undefined
          }
        }

        return null
      })
      .filter((row) => row !== null) as CatalogTableRow[]
  }

  // Apply filters
  const query = searchQuery.value.trim().toLowerCase()

  return filterHierarchy(data, query)
})

// Helper function to count items recursively in hierarchical data
const countItemsRecursively = (rows: CatalogTableRow[], type: string): number => {
  let count = 0
  rows.forEach((row) => {
    if (row.type === type) {
      count++
    }
    if (row.children) {
      count += countItemsRecursively(row.children, type)
    }
  })
  return count
}

const totalVisibleTables = computed(() => countItemsRecursively(filteredData.value, 'table'))

const totalVisibleColumns = computed(() => countItemsRecursively(filteredData.value, 'column'))

const totalSchemas = computed(() => countItemsRecursively(filteredData.value, 'schema'))

// TanStack Table instance
const table = useVueTable({
  data: filteredData,
  columns,
  getCoreRowModel: getCoreRowModel(),
  getExpandedRowModel: getExpandedRowModel(),
  getFilteredRowModel: getFilteredRowModel(),
  getSubRows: (row) => row.children,
  state: {
    get expanded() {
      return expanded.value
    }
  },
  onExpandedChange: (updater) => {
    expanded.value = typeof updater === 'function' ? updater(expanded.value) : updater
  },
  enableExpanding: true
})

// Methods
function getRowClass(row: CatalogTableRow) {
  const baseClass = 'hover:bg-gray-50 cursor-pointer'

  if (row.type === 'schema') {
    return `${baseClass} bg-gray-50 border-b border-gray-200`
  }
  if (row.type === 'table') {
    return `${baseClass} border-b border-gray-100`
  }
  return `${baseClass} border-b border-gray-50`
}

function onSearch() {
  // Clear existing timeout
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
  }

  // Set new timeout for debounced search
  searchTimeout.value = setTimeout(() => {
    // Search is handled by computed properties, nothing to do here
    // But we could trigger additional API calls if needed
  }, 300)
}

async function refresh() {
  if (contextsStore.contextSelected) {
    await catalogStore.fetchAssets(contextsStore.contextSelected.id, undefined, 1000) // Load more assets
  }
}

function fillDescription(rowData: CatalogTableRow) {
  let prompt = ''

  if (rowData.type === 'table') {
    const tableName =
      rowData.asset?.name || rowData.asset?.table_facet?.table_name || 'Unknown Table'
    const schemaName = rowData.asset?.table_facet?.schema || 'default'
    prompt = `Please provide a description for the table '${tableName}' in schema '${schemaName}'. Consider what data this table might contain based on its name and structure.`
  } else if (rowData.type === 'column') {
    const columnName = rowData.asset?.column_facet?.column_name || 'Unknown Column'
    const dataType = rowData.asset?.column_facet?.data_type || 'unknown'

    // Find parent table info
    const parentTableId = rowData.asset?.column_facet?.parent_table_asset_id
    let tableName = 'Unknown Table'
    if (parentTableId) {
      const parentTable = catalogStore.assetsArray.find((a) => a.id === parentTableId)
      if (parentTable) {
        tableName = parentTable.name || parentTable.table_facet?.table_name || 'Unknown Table'
      }
    }

    prompt = `Please provide a description for the column '${columnName}' of type '${dataType}' in table '${tableName}'. Consider what this column represents and what kind of data it might store.`
  }

  // Navigate to chat with the prompt
  router.push({
    path: '/chat/new',
    query: { prompt: prompt }
  })
}

// Load assets when component mounts and we have a context but no assets
onMounted(async () => {
  if (contextsStore.contextSelected && catalogStore.assetsArray.length === 0) {
    await catalogStore.fetchAssets(contextsStore.contextSelected.id, undefined, 1000)
  }
})

watch(
  () => contextsStore.contextSelected,
  async (newContext, oldContext) => {
    if (newContext && newContext.id !== oldContext?.id) {
      expanded.value = {}
      searchQuery.value = ''
      // Fetch assets for new context if needed
      if (catalogStore.assetsArray.length === 0) {
        await catalogStore.fetchAssets(newContext.id, undefined, 1000)
      }
    }
  }
)

// Auto-expand first schema if there's only one
watch(
  groupedAssets,
  (schemas) => {
    if (schemas.length === 1 && Object.keys(expanded.value).length === 0) {
      const firstSchemaId = `schema-${schemas[0].name}`
      expanded.value = { [firstSchemaId]: true }
    }
  },
  { immediate: true }
)
</script>
