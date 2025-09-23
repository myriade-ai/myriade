<template>
  <div class="relative">
    <div class="rounded-md border">
      <Table class="">
        <TableHeader>
          <TableRow>
            <TableHead
              v-for="column in columns"
              :key="column"
              class="font-medium cursor-pointer select-none hover:bg-muted/50"
              @click="toggleSort(column)"
            >
              <div class="flex items-center justify-between">
                <span>{{ column }}</span>
                <div class="flex flex-col ml-2">
                  <ChevronUp
                    :class="[
                      'h-3 w-3 transition-colors',
                      sortConfig.column === column && sortConfig.direction === 'asc'
                        ? 'text-foreground'
                        : 'text-muted-foreground/40'
                    ]"
                  />
                  <ChevronDown
                    :class="[
                      'h-3 w-3 -mt-1 transition-colors',
                      sortConfig.column === column && sortConfig.direction === 'desc'
                        ? 'text-foreground'
                        : 'text-muted-foreground/40'
                    ]"
                  />
                </div>
              </div>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-for="(row, index) in paginatedData" :key="index">
            <TableCell v-for="column in columns" :key="column" class="py-2">
              <span class="break-words max-w-xs inline-block overflow-hidden text-ellipsis">
                {{ formatCellValue(row[column]) }}
              </span>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>

    <!-- Pagination -->
    <div v-if="filteredData.length > pageSize" class="flex items-center justify-between px-2 py-4">
      <div class="text-sm text-muted-foreground">
        Showing {{ startRow }}-{{ endRow }} of {{ totalCount }} rows
      </div>
      <div class="flex items-center space-x-2">
        <Button size="sm" variant="ghost" @click="copyToClipboard">
          {{ copyText }}
        </Button>
        <Button variant="outline" size="sm" :disabled="currentPage === 1" @click="previousPage">
          Previous
        </Button>
        <div class="text-sm">Page {{ currentPage }} of {{ totalPages }}</div>
        <Button
          variant="outline"
          size="sm"
          :disabled="currentPage === totalPages"
          @click="nextPage"
        >
          Next
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ChevronDown, ChevronUp } from 'lucide-vue-next'
import { Button } from './ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table'

const props = defineProps<{
  data: Record<string, unknown>[]
  count?: number
}>()

const copyText = ref('Copy as XLSX')
const currentPage = ref(1)
const pageSize = 10

// Sorting state
const sortConfig = ref<{
  column: string | null
  direction: 'asc' | 'desc'
}>({
  column: null,
  direction: 'asc'
})

const filteredData = computed(() => {
  let data = props.data.map((row) => {
    const newRow = { ...row }
    for (const key in newRow) {
      if (typeof newRow[key] === 'string' && (newRow[key] as string).startsWith('encrypted:')) {
        newRow[key] = '***hidden***'
      }
    }
    return newRow
  })

  if (sortConfig.value.column) {
    data = data.sort((a, b) => {
      const aVal = a[sortConfig.value.column!]
      const bVal = b[sortConfig.value.column!]

      if (aVal == null && bVal == null) return 0
      if (aVal == null) return 1
      if (bVal == null) return -1

      const aStr = String(aVal).toLowerCase()
      const bStr = String(bVal).toLowerCase()

      const aNum = Number(aVal)
      const bNum = Number(bVal)
      if (!isNaN(aNum) && !isNaN(bNum)) {
        const comparison = aNum - bNum
        return sortConfig.value.direction === 'asc' ? comparison : -comparison
      }

      const comparison = aStr.localeCompare(bStr)
      return sortConfig.value.direction === 'asc' ? comparison : -comparison
    })
  }

  return data
})

// Dynamically determine columns from data keys
const columns = computed(() => {
  if (!filteredData.value.length) return []
  const allKeys = new Set<string>()
  filteredData.value.forEach((row) => {
    Object.keys(row).forEach((key) => allKeys.add(key))
  })
  return Array.from(allKeys)
})

const totalPages = computed(() => Math.ceil(filteredData.value.length / pageSize))
const totalCount = computed(() => props.count ?? filteredData.value.length)

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return filteredData.value.slice(start, end)
})

const startRow = computed(() => (currentPage.value - 1) * pageSize + 1)
const endRow = computed(() => Math.min(currentPage.value * pageSize, filteredData.value.length))

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

const previousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const formatCellValue = (value: unknown): string => {
  if (value === null) return 'null'
  if (value === undefined) return 'undefined'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

const toggleSort = (column: string) => {
  if (sortConfig.value.column === column) {
    sortConfig.value.direction = sortConfig.value.direction === 'asc' ? 'desc' : 'asc'
  } else {
    sortConfig.value.column = column
    sortConfig.value.direction = 'asc'
  }
  // Reset to first page when sorting changes
  currentPage.value = 1
}

const copyToClipboard = async () => {
  try {
    // Convert data to TSV format for clipboard
    const headers = columns.value.join('\t')
    const rows = filteredData.value
      .map((row) => columns.value.map((col) => formatCellValue(row[col])).join('\t'))
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
