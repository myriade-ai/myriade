<template>
  <div class="relative">
    <div class="rounded-md border overflow-x-auto">
      <Table :style="{ minWidth: `${table.getCenterTotalSize()}px` }" class="bg-background">
        <TableHeader>
          <TableRow v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
            <TableHead
              v-for="header in headerGroup.headers"
              :key="header.id"
              class="font-medium select-none bg-muted/50 hover:bg-muted relative"
              :style="{
                width: `${header.getSize()}px`,
                minWidth: `${header.getSize()}px`,
                maxWidth: `${header.getSize()}px`
              }"
            >
              <div
                class="flex items-center justify-between overflow-hidden cursor-pointer"
                @click="header.column.getToggleSortingHandler()?.($event)"
              >
                <div class="truncate flex-1 min-w-0">
                  <FlexRender
                    :render="header.column.columnDef.header"
                    :props="header.getContext()"
                  />
                </div>
                <div v-if="header.column.getIsSorted()" class="flex flex-col ml-2 flex-shrink-0">
                  <ChevronUp
                    :class="[
                      'h-3 w-3 transition-colors',
                      header.column.getIsSorted() === 'asc'
                        ? 'text-foreground'
                        : 'text-muted-foreground/40'
                    ]"
                  />
                  <ChevronDown
                    :class="[
                      'h-3 w-3 -mt-1 transition-colors',
                      header.column.getIsSorted() === 'desc'
                        ? 'text-foreground'
                        : 'text-muted-foreground/40'
                    ]"
                  />
                </div>
              </div>
              <div
                v-if="header.column.getCanResize()"
                class="resizer"
                :class="{ isResizing: header.column.getIsResizing() }"
                :style="{
                  transform:
                    columnResizeMode === 'onEnd' && header.column.getIsResizing()
                      ? `translateX(${table.getState().columnSizingInfo.deltaOffset ?? 0}px)`
                      : ''
                }"
                @dblclick.stop="header.column.resetSize()"
                @mousedown.stop="header.getResizeHandler()?.($event)"
                @touchstart.stop="header.getResizeHandler()?.($event)"
              />
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-if="!table.getRowModel().rows.length">
            <TableCell
              :colspan="columns.length"
              class="text-center text-sm text-muted-foreground py-4"
            >
              No data available.
            </TableCell>
          </TableRow>
          <TableRow v-for="row in table.getRowModel().rows" :key="row.id">
            <TableCell
              v-for="cell in row.getVisibleCells()"
              :key="cell.id"
              class="py-2"
              :style="{
                width: `${cell.column.getSize()}px`,
                minWidth: `${cell.column.getSize()}px`,
                maxWidth: `${cell.column.getSize()}px`
              }"
            >
              <div class="truncate overflow-hidden text-ellipsis">
                <FlexRender :render="cell.column.columnDef.cell" :props="cell.getContext()" />
              </div>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>

    <!-- Pagination -->
    <div v-if="props.data.length > pageSize" class="flex items-center justify-between px-2 py-4">
      <div class="text-sm text-muted-foreground">
        Showing {{ startRow }}-{{ endRow }} of {{ totalCount }} rows
      </div>
      <div class="flex items-center space-x-2">
        <Button size="sm" variant="ghost" @click="copyToClipboard">
          {{ copyText }}
        </Button>
        <Button
          variant="outline"
          size="sm"
          :disabled="!table.getCanPreviousPage()"
          @click="table.previousPage()"
        >
          Previous
        </Button>
        <div class="text-sm">
          Page {{ table.getState().pagination.pageIndex + 1 }} of {{ table.getPageCount() }}
        </div>
        <Button
          variant="outline"
          size="sm"
          :disabled="!table.getCanNextPage()"
          @click="table.nextPage()"
        >
          Next
        </Button>
      </div>
    </div>

    <div v-else class="flex justify-end px-2 py-4">
      <Button size="sm" variant="ghost" @click="copyToClipboard">
        {{ copyText }}
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  FlexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useVueTable,
  type ColumnDef,
  type SortingState
} from '@tanstack/vue-table'
import { ChevronDown, ChevronUp } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { Button } from './ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table'

const props = defineProps<{
  data: Record<string, unknown>[]
  count?: number
  columns?: Array<{ name: string }>
}>()

const copyText = ref('Copy as XLSX')
const pageSize = 10
const sorting = ref<SortingState>([])
const columnSizing = ref<Record<string, number>>({})
const columnResizeMode = ref<'onChange' | 'onEnd'>('onChange')
const pagination = ref({
  pageIndex: 0,
  pageSize: pageSize
})

const processedData = computed(() => {
  return props.data.map((row) => {
    const newRow = { ...row }
    for (const key in newRow) {
      if (typeof newRow[key] === 'string' && (newRow[key] as string).startsWith('encrypted:')) {
        newRow[key] = '***hidden***'
      }
    }
    return newRow
  })
})

const formatCellValue = (value: unknown): string => {
  if (value === null) return 'null'
  if (value === undefined) return 'undefined'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

const columns = computed<ColumnDef<Record<string, unknown>>[]>(() => {
  // If we have no data but columns are provided, use them
  if (!processedData.value.length && props.columns) {
    return props.columns.map((col) => ({
      accessorKey: col.name,
      header: col.name,
      cell: (info) => formatCellValue(info.getValue()),
      enableSorting: true,
      enableResizing: true,
      size: 150,
      minSize: 30,
      maxSize: 1000
    }))
  }

  // If we have no data and no columns provided, return empty
  if (!processedData.value.length) return []

  const allKeys = new Set<string>()
  processedData.value.forEach((row) => {
    Object.keys(row).forEach((key) => allKeys.add(key))
  })
  const keysArray = Array.from(allKeys)

  return keysArray.map((key) => ({
    accessorKey: key,
    header: key,
    cell: (info) => formatCellValue(info.getValue()),
    enableSorting: true,
    enableResizing: true,
    size: 150,
    minSize: 30,
    maxSize: 1000
  }))
})

const table = useVueTable({
  get data() {
    return processedData.value
  },
  get columns() {
    return columns.value
  },
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  onSortingChange: (updater) => {
    sorting.value = typeof updater === 'function' ? updater(sorting.value) : updater
  },
  onColumnSizingChange: (updater) => {
    columnSizing.value = typeof updater === 'function' ? updater(columnSizing.value) : updater
  },
  onPaginationChange: (updater) => {
    pagination.value = typeof updater === 'function' ? updater(pagination.value) : updater
  },
  state: {
    get sorting() {
      return sorting.value
    },
    get columnSizing() {
      return columnSizing.value
    },
    get pagination() {
      return pagination.value
    }
  },
  columnResizeMode: columnResizeMode.value,
  enableColumnResizing: true
})

const totalCount = computed(() => props.count ?? processedData.value.length)
const startRow = computed(
  () => table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1
)
const endRow = computed(() =>
  Math.min(
    (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
    processedData.value.length
  )
)

const copyToClipboard = async () => {
  try {
    // Convert data to TSV format for clipboard
    const headers = columns.value.map((col) => String(col.header)).join('\t')
    const rows = processedData.value
      .map((row) =>
        // @ts-expect-error We know accessorKey is available here because we defined it above
        columns.value.map((col) => formatCellValue(row[String(col.accessorKey)])).join('\t')
      )
      .join('\n')
    const tsvData = headers + '\n' + rows

    await navigator.clipboard.writeText(tsvData)
    copyText.value = 'Copied!'
    setTimeout(() => {
      copyText.value = 'Copy as XLSX'
    }, 1000)
  } catch (error) {
    console.error('Failed to copy to clipboard:', error)
  }
}
</script>

<style scoped>
.resizer {
  position: absolute;
  top: 0;
  right: 0;
  height: 100%;
  width: 4px;
  cursor: col-resize;
  user-select: none;
  touch-action: none;
  transition: background 0.2s ease;
}

.resizer:hover {
  background: hsl(var(--primary) / 0.5);
  border-right: 1px solid black;
}

.resizer.isResizing {
  background: black;
  border-right: 2px solid black;
}
</style>
