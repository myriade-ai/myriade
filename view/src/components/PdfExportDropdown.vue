<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <slot name="trigger">
        <Button variant="outline" size="sm" :disabled="isExporting">
          <Download class="w-4 h-4 mr-2" />
          Export
        </Button>
      </slot>
    </DropdownMenuTrigger>
    <DropdownMenuContent class="w-64 p-0">
      <DropdownMenuLabel class="px-3 py-2 space-y-1">
        <div class="font-medium">Export Options</div>
        <div class="text-xs text-muted-foreground font-normal">Customize your export</div>
      </DropdownMenuLabel>
      <DropdownMenuSeparator />
      <div class="px-3 py-2 flex items-center justify-between gap-3">
        <label for="include-sql" class="text-sm cursor-pointer flex-1">
          Include SQL statements
        </label>
        <Switch id="include-sql" v-model="includeSql" />
      </div>
      <DropdownMenuSeparator />
      <DropdownMenuItem @click="handleExport" :disabled="isExporting" class="cursor-pointer mb-1">
        <Download class="w-4 h-4 mr-2" />
        <span v-if="isExporting" class="flex items-center gap-2">
          <Loader2 class="animate-spin h-4 w-4" />
          Exporting...
        </span>
        <span v-else>Download PDF</span>
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template>

<script setup lang="ts">
import Button from '@/components/ui/button/Button.vue'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { Switch } from '@/components/ui/switch'
import axios from '@/plugins/axios'
import { Download, Loader2 } from 'lucide-vue-next'
import { ref } from 'vue'

interface Props {
  documentId: string
  documentTitle?: string
}

const props = defineProps<Props>()

const includeSql = ref(true)
const isExporting = ref(false)

const buildPdfFilename = () => {
  const rawTitle = props.documentTitle?.trim() || 'report'
  const sanitized = rawTitle.replace(/[^a-zA-Z0-9-_]+/g, '_').replace(/^_+|_+$/g, '')
  return `${sanitized || 'report'}.pdf`
}

const handleExport = async () => {
  try {
    isExporting.value = true
    const response = await axios.post(
      `/api/documents/${props.documentId}/export`,
      { includeSql: includeSql.value },
      { responseType: 'blob' }
    )

    const blob =
      response.data instanceof Blob
        ? response.data
        : new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = window.document.createElement('a')
    link.href = url
    link.download = buildPdfFilename()
    window.document.body.appendChild(link)
    link.click()
    window.document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to export document:', error)
    alert('Failed to export PDF. Please try again.')
  } finally {
    isExporting.value = false
  }
}
</script>
