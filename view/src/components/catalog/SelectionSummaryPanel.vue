<template>
  <transition name="slide-up">
    <div
      v-if="catalogStore.selectionMode"
      class="fixed bottom-4 right-4 z-50 bg-white rounded-lg shadow-xl border border-slate-200 max-w-md w-full"
    >
      <div class="px-4 py-3 border-b border-slate-200 bg-slate-50">
        <div class="flex items-center justify-between">
          <div class="flex flex-col gap-1">
            <h3 class="font-semibold text-sm">Selected Assets</h3>
            <div class="flex items-center gap-2 text-xs text-muted-foreground">
              <template v-if="catalogStore.selectedAssets.length > 0">
                <span v-if="catalogStore.selectedAssetsGrouped.tables.length > 0">
                  {{ catalogStore.selectedAssetsGrouped.tables.length }} table{{
                    catalogStore.selectedAssetsGrouped.tables.length !== 1 ? 's' : ''
                  }}
                </span>
                <span
                  v-if="
                    catalogStore.selectedAssetsGrouped.tables.length > 0 &&
                    catalogStore.selectedAssetsGrouped.columns.length > 0
                  "
                  class="text-slate-300"
                >
                  •
                </span>
                <span v-if="catalogStore.selectedAssetsGrouped.columns.length > 0">
                  {{ catalogStore.selectedAssetsGrouped.columns.length }} column{{
                    catalogStore.selectedAssetsGrouped.columns.length !== 1 ? 's' : ''
                  }}
                </span>
              </template>
              <span v-else>No assets selected yet</span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            class="h-6 w-6"
            @click="catalogStore.clearSelection"
            title="Clear selection"
          >
            <XIcon class="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div class="max-h-64 overflow-y-auto p-2 space-y-1">
        <!-- Empty State -->
        <div
          v-if="catalogStore.selectedAssets.length === 0"
          class="flex flex-col items-center justify-center py-8 px-4 text-center"
        >
          <div class="rounded-full bg-slate-100 p-3 mb-3">
            <SparklesIcon class="h-6 w-6 text-slate-400" />
          </div>
          <p class="text-sm text-muted-foreground mb-1">Click on assets to select them</p>
          <p class="text-xs text-muted-foreground">
            Use the "Add to Analysis" button on tables or columns
          </p>
        </div>

        <!-- Tables -->
        <div v-if="catalogStore.selectedAssetsGrouped.tables.length > 0">
          <p class="text-xs font-medium text-muted-foreground px-2 py-1">Tables</p>
          <div
            v-for="table in catalogStore.selectedAssetsGrouped.tables"
            :key="table.id"
            class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-50 group"
          >
            <Table class="h-4 w-4 text-primary-600 flex-shrink-0" />
            <span class="text-sm truncate flex-1">
              {{ table.name || table.table_facet?.table_name }}
            </span>
            <Button
              variant="ghost"
              size="icon"
              class="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
              @click="catalogStore.toggleAssetSelection(table.id, true)"
              title="Remove from selection"
            >
              <XIcon class="h-3 w-3" />
            </Button>
          </div>
        </div>

        <!-- Columns -->
        <div v-if="catalogStore.selectedAssetsGrouped.columns.length > 0">
          <p class="text-xs font-medium text-muted-foreground px-2 py-1 mt-2">Columns</p>
          <div
            v-for="column in catalogStore.selectedAssetsGrouped.columns"
            :key="column.id"
            class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-50 group"
          >
            <Columns3 class="h-4 w-4 text-primary-600 flex-shrink-0" />
            <span class="text-sm truncate flex-1">
              {{ column.column_facet?.parent_table_facet?.table_name }}.{{
                column.column_facet?.column_name
              }}
            </span>
            <Button
              variant="ghost"
              size="icon"
              class="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
              @click="catalogStore.toggleAssetSelection(column.id, false)"
              title="Remove from selection"
            >
              <XIcon class="h-3 w-3" />
            </Button>
          </div>
        </div>
      </div>

      <div class="px-4 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between gap-3">
        <p class="text-xs text-muted-foreground">
          {{ catalogStore.selectedAssets.length > 0 ? 'Ready to review these assets with AI' : 'Select assets to start analysis' }}
        </p>
        <Button
          @click="analyzeSelected"
          size="sm"
          :disabled="catalogStore.selectedAssets.length === 0"
        >
          <SparklesIcon class="h-4 w-4" />
          Analyze Selected
        </Button>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useCatalogStore } from '@/stores/catalog'
import { useConversationsStore } from '@/stores/conversations'
import { useContextsStore } from '@/stores/contexts'
import { Table, Columns3, XIcon, SparklesIcon } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const catalogStore = useCatalogStore()
const conversationsStore = useConversationsStore()
const contextsStore = useContextsStore()
const router = useRouter()

async function analyzeSelected() {
  const { tables, columns } = catalogStore.selectedAssetsGrouped

  const tablesList = tables
    .map((t) => `- ${t.name || t.table_facet?.table_name} (id: ${t.id})`)
    .join('\n')
  const columnsList = columns
    .map(
      (c) =>
        `- ${c.column_facet?.parent_table_facet?.table_name}.${c.column_facet?.column_name} (id: ${c.id})`
    )
    .join('\n')

  const prompt = `Please review and help fill in descriptions for the following selected assets in our data catalog:

${tables.length > 0 ? `**Tables:**\n${tablesList}\n` : ''}
${columns.length > 0 ? `**Columns:**\n${columnsList}\n` : ''}

Before writing any asset descriptions, please:

1. **Perform a global business understanding check**:
   - Analyze the overall database structure and schema
   - Identify key business domains and data relationships
   - Understand the primary business processes reflected in the data

2. **Prioritize assets for description**:
   - Identify core tables and columns
   - Consider tables with the most relationships or references

3. **Write short and concise asset descriptions that include**:
   - Key relationships with other tables
   - Data freshness and update patterns if observable
   - Important business rules or constraints
   - Relevant tags based on business domain, data sensitivity, usage patterns, and data quality characteristics

Please start by exploring the database structure to understand our business context, then provide descriptions for the most important assets you identify. Focus on clarity and business value rather than technical implementation details.`

  if (!contextsStore.contextSelected) {
    console.error('No context selected')
    return
  }

  try {
    const newConversation = await conversationsStore.createConversation(
      contextsStore.contextSelected.id
    )

    await conversationsStore.sendMessage(newConversation.id, prompt, 'text')

    router.push({ name: 'ChatPage', params: { id: newConversation.id.toString() } })
  } catch (error) {
    console.error('Error creating conversation and sending message:', error)
  }
}
</script>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(100%);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(20px);
  opacity: 0;
}
</style>
