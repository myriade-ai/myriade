<template>
  <div class="overflow-hidden">
    <!-- Database Header -->
    <div class="px-6 py-4 bg-card">
      <!-- First row: Database name, progress bar, percentage -->
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-3">
          <Database class="h-5 w-5 text-muted-foreground" />
          <h3 class="font-semibold text-sm text-foreground">{{ database.database_name }}</h3>
        </div>
        <ProgressBar :percentage="database.completion_percentage" size="sm" />
      </div>

      <!-- Second row: Metadata -->
      <div class="flex items-center justify-between text-xs text-muted-foreground">
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
        class="w-full px-6 py-3 flex items-center justify-between hover:bg-muted transition-colors border-t border-border text-left bg-muted/80 dark:bg-muted/30 cursor-pointer"
        @click="isExpanded = !isExpanded"
      >
        <span
          class="text-xs font-semibold text-foreground uppercase tracking-wide flex items-center gap-2"
        >
          <ChevronRight v-if="!isExpanded" class="h-4 w-4 text-muted-foreground" />
          <ChevronDown v-else class="h-4 w-4 text-muted-foreground" />
          Schemas
        </span>
      </button>

      <!-- Schemas List -->
      <div v-show="isExpanded" class="divide-y divide-border bg-muted/30 dark:bg-muted/10">
        <div
          v-for="schema in sortedSchemas"
          :key="schema.schema_name"
          class="px-6 py-3 hover:bg-muted transition-colors flex items-center justify-between gap-4"
        >
          <div class="flex items-center gap-3 flex-1 min-w-0">
            <FolderTree class="h-4 w-4 text-muted-foreground flex-shrink-0" />
            <span class="text-sm font-medium text-foreground truncate">{{
              schema.schema_name
            }}</span>
            <ProgressBar :percentage="schema.completion_percentage" size="sm" />
            <span class="text-sm text-muted-foreground flex-shrink-0"
              >{{ schema.table_count }} tables</span
            >
          </div>
          <div class="flex items-center flex-shrink-0">
            <Button
              @click.stop="handleCatalogClick(schema)"
              variant="ghost"
              size="sm"
              class="text-gold hover:text-gold/80"
            >
              {{ isSchemaRunning(schema.schema_asset_id) ? 'Running...' : 'Run catalog' }}
              <LoaderIcon v-if="isSchemaRunning(schema.schema_asset_id)" :width="16" :height="16" />
              <SparklesIcon v-else class="h-3 w-3" />
            </Button>
            <Button
              @click.stop="navigateToSchema(schema.schema_asset_id)"
              variant="ghost"
              size="sm"
              class="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium whitespace-nowrap"
            >
              View →
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="px-6 py-3 text-center bg-muted/30">
      <p class="text-xs text-muted-foreground">No schemas found</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DatabaseStats, SchemaStats } from '@/composables/useDashboardStats'
import { Button } from '../ui/button'
import LoaderIcon from '@/components/icons/LoaderIcon.vue'
import { useContextsStore } from '@/stores/contexts'
import { useConversationsStore, STATUS } from '@/stores/conversations'
import { ChevronDown, ChevronRight, Database, FolderTree, SparklesIcon } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import ProgressBar from './ProgressBar.vue'

interface Props {
  database: DatabaseStats
}

const props = defineProps<Props>()
const router = useRouter()
const contextsStore = useContextsStore()
const conversationsStore = useConversationsStore()

const isExpanded = ref(true)

// Get the running conversation ID for a schema, or null if not running
function getRunningConversationId(schemaAssetId: string): string | null {
  for (const [convId, status] of Object.entries(conversationsStore.conversationStatuses)) {
    if (status.status !== STATUS.RUNNING && status.status !== STATUS.PENDING) {
      continue
    }
    const conversation = conversationsStore.getConversationById(convId)
    // Check conversation name (available after refresh) or first message content
    const nameMatches = conversation?.name?.includes(schemaAssetId)
    const firstMessageMatches = conversation?.messages?.[0]?.content?.includes(schemaAssetId)
    if (nameMatches || firstMessageMatches) {
      return convId
    }
  }
  return null
}

function isSchemaRunning(schemaAssetId: string): boolean {
  return getRunningConversationId(schemaAssetId) !== null
}

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

async function handleCatalogClick(schema: SchemaStats) {
  // If already running, navigate to the conversation
  const runningConvId = getRunningConversationId(schema.schema_asset_id)
  if (runningConvId) {
    router.push({ name: 'ChatPage', params: { id: runningConvId } })
    return
  }

  // Otherwise, start a new catalog run
  const context = contextsStore.contextSelected
  if (!context) {
    console.error('No context selected')
    return
  }

  const prompt = `Document the tables inside "${schema.schema_name} - ${schema.schema_asset_id}".`

  try {
    const conversation = await conversationsStore.createConversation(context.id)
    await conversationsStore.sendMessage(conversation.id, prompt, 'text')
    // Stay on dashboard - don't navigate
  } catch (error) {
    console.error('Error creating catalog conversation:', error)
  }
}
</script>
