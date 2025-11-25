<template>
  <Card
    :class="
      cn(
        'transition-shadow rounded-xl hover:border-primary-600',
        props.selected ? 'ring-2 ring-primary-500 shadow-md' : ''
      )
    "
    :id="props.asset.id"
  >
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <component :is="iconByType[props.asset.type]" class="w-5 h-5" />
        <span>{{ props.asset.name }}</span>
      </CardTitle>
      <CardDescription class="flex flex-wrap items-center gap-1">
        <Badge
          :class="
            cn(
              props.asset.type === 'TABLE'
                ? 'bg-blue-100 text-blue-800'
                : 'bg-green-100 text-green-800'
            )
          "
          >{{ props.asset.type }}</Badge
        >

        <p v-if="props.asset.type === 'COLUMN'" class="text-sm text-muted-foreground">
          from {{ columnOrigin }}
        </p>
        <p v-else-if="props.asset.type === 'TABLE'" class="text-sm text-muted-foreground">
          from {{ props.asset.schema }}
        </p>
      </CardDescription>
      <CardAction class="flex flex-wrap items-center justify-end gap-2">
        <!-- Status Badge -->
        <AssetBadgeStatus :status="props.asset.status" />

        <Tooltip v-if="props.asset.status === 'draft'" :disabled="!hasAiSuggestions">
          <TooltipTrigger as-child>
            <Button
              @click="handlePublish"
              size="sm"
              class="disabled:pointer-events-auto"
              :disabled="isProcessing || hasAiSuggestions"
              :is-loading="publishing"
            >
              <template #loading>Publishing...</template>
              Publish
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Accept or reject suggested changes before publishing</p>
          </TooltipContent>
        </Tooltip>

        <!-- Navigate to catalog button -->
        <Button
          variant="ghost"
          size="icon"
          class="text-muted-foreground"
          :disabled="isProcessing"
          @click="handleNavigateToCatalog"
        >
          <span class="sr-only">Open asset in catalog</span>
          <ExternalLink class="w-4 h-4" />
        </Button>
      </CardAction>
    </CardHeader>
    <CardContent>
      <!-- Note Alert (always show if present) - Moved to top -->
      <div
        v-if="props.asset.note"
        class="flex items-start gap-3 p-3 rounded-lg bg-blue-50 border-blue-200 text-blue-900 mb-4"
      >
        <Info class="size-4 mt-0.5 flex-shrink-0 text-blue-600" />
        <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ props.asset.note }}</p>
      </div>

      <!-- Description Edit -->
      <div class="space-y-2">
        <label class="text-xs font-medium text-muted-foreground">Description</label>

        <!-- AI Suggestion Diff View -->
        <div v-if="props.asset.ai_suggestion" class="overflow-hidden bg-card border rounded-md">
          <div class="space-y-0 text-xs font-mono leading-relaxed">
            <!-- Before (removal) -->
            <div class="bg-red-50 dark:bg-red-900/20 px-2 py-1 border-l-2 border-red-400">
              <span class="text-red-600 select-none mr-2">−</span>
              <span class="text-red-900 dark:text-red-200">{{
                props.asset.description || ''
              }}</span>
            </div>
            <!-- After (addition) - Editable -->
            <div class="bg-green-50 dark:bg-green-900/20 px-2 py-1 border-l-2 border-green-400">
              <span class="text-green-600 select-none mr-2">+</span>
              <Textarea
                v-model="editableSuggestion"
                rows="3"
                class="inline-block align-top w-[calc(100%-1.5rem)] border-0 p-0 text-xs font-mono text-green-900 dark:text-green-200 bg-transparent focus:ring-0 focus:ring-offset-0 focus:outline-none focus:border-0 focus-visible:ring-0 focus-visible:ring-offset-0 resize-none leading-relaxed shadow-none"
                :disabled="isProcessing"
                placeholder="Edit AI suggestion..."
              />
            </div>
          </div>
          <!-- Action buttons for description -->
          <div class="px-2 py-2 bg-gray-50 dark:bg-gray-800 border-t flex justify-end gap-2">
            <Button
              @click="handleRejectDescription"
              size="sm"
              variant="ghost"
              :disabled="isProcessing"
            >
              Reject
            </Button>
            <Button
              @click="handleApproveDescription"
              size="sm"
              :disabled="isProcessing || !editableSuggestion.trim()"
              :is-loading="isProcessing"
            >
              <template #loading>Accepting...</template>
              Accept changes
            </Button>
          </div>
        </div>

        <!-- Regular Description textarea (when no AI suggestion) -->
        <Textarea
          v-else
          v-model="draft.description"
          rows="4"
          class="max-h-72"
          :disabled="isProcessing"
          placeholder="Add description..."
        />
      </div>

      <!-- Tags Section -->
      <div class="space-y-2">
        <label class="text-xs font-medium text-muted-foreground">Tags</label>

        <!-- AI Suggested Tags Diff View -->
        <div
          v-if="props.asset.ai_suggested_tags && props.asset.ai_suggested_tags.length > 0"
          class="overflow-hidden bg-card border rounded-md"
        >
          <div class="space-y-0">
            <!-- Before (removal) - Current tags -->
            <div class="bg-red-50 dark:bg-red-900/20 px-3 py-2 border-l-2 border-red-400">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-red-600 select-none">−</span>
                <div v-if="props.asset.tags.length > 0" class="flex items-center gap-1 flex-wrap">
                  <Badge
                    v-for="tag in props.asset.tags"
                    :key="tag.id"
                    variant="outline"
                    class="text-red-900 dark:text-red-200 border-red-200"
                  >
                    {{ tag.name }}
                  </Badge>
                </div>
                <span v-else class="text-red-900 dark:text-red-200 text-sm italic">No tags</span>
              </div>
            </div>
            <!-- After (addition) - Show only NEW suggested tags in diff -->
            <div
              v-if="newSuggestedTags.length > 0"
              class="bg-green-50 dark:bg-green-900/20 px-3 py-2 border-l-2 border-green-400"
            >
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-green-600 select-none">+</span>
                <div class="flex items-center gap-1 flex-wrap">
                  <Badge
                    v-for="tag in newSuggestedTags"
                    :key="tag.id"
                    variant="outline"
                    class="text-green-900 dark:text-green-200 border-green-200"
                  >
                    {{ tag.name }}
                  </Badge>
                </div>
              </div>
            </div>
            <!-- Edit all tags section -->
            <div class="px-3 py-2 border-t border-border">
              <label class="text-xs font-medium text-muted-foreground mb-2 block">Edit Tags</label>
              <AssetTagSelect
                v-model="editableSuggestedTags"
                :disabled="isProcessing"
                class="bg-transparent border-0"
              />
            </div>
            <!-- Action buttons for tags -->
            <div class="px-3 py-2 bg-gray-50 dark:bg-gray-800 border-t flex justify-end gap-2">
              <Button @click="handleRejectTags" size="sm" variant="ghost" :disabled="isProcessing">
                Reject
              </Button>
              <Button
                @click="handleApproveTags"
                size="sm"
                :disabled="isProcessing"
                :is-loading="isProcessing"
              >
                <template #loading>Accepting...</template>
                Accept changes
              </Button>
            </div>
          </div>
        </div>

        <!-- Regular Tags Select (when no AI suggestions) -->
        <AssetTagSelect v-else v-model="draft.tags" :disabled="isProcessing" />
      </div>

      <!-- Action buttons -->
      <div class="flex justify-end gap-2 pt-2">
        <Button
          v-if="hasChanges"
          @click="handleSave"
          size="sm"
          variant="outline"
          :disabled="isProcessing"
          :is-loading="isProcessing"
        >
          <template #loading>Saving...</template>
          Save
        </Button>
      </div>
    </CardContent>
  </Card>
</template>

<script lang="ts" setup>
import { cn } from '@/lib/utils'
import {
  useCatalogStore,
  type AssetStatus,
  type AssetTag,
  type AssetType,
  type Privacy
} from '@/stores/catalog'
import { Columns3, Database, ExternalLink, FolderTree, Info } from 'lucide-vue-next'
import { computed, reactive, ref, watch, type Component } from 'vue'
import AssetBadgeStatus from './AssetBadgeStatus.vue'
import AssetTagSelect from './AssetTagSelect.vue'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Textarea } from './ui/textarea'
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip'

interface AssetInput {
  id: string
  type: AssetType
  name: string
  description?: string | null
  dataType?: string | null
  privacy?: Privacy
  tags: AssetTag[]
  schema?: string | null
  tableName?: string | null
  status?: AssetStatus
  ai_suggestion?: string | null
  note?: string | null
  ai_suggested_tags?: string[] | null
  published_by?: string | null
  published_at?: string | null
}

const props = defineProps<{
  asset: AssetInput
  isProcessing?: boolean
  selected?: boolean
}>()

const emit = defineEmits<{
  (e: 'save', payload: { id: string; description: string; tag_ids: string[] }): void
  (e: 'navigate-to-catalog', payload: { id: string }): void
  (e: 'publish', payload: { id: string }): void
  (e: 'approve-description', payload: { id: string; description: string }): void
  (e: 'approve-tags', payload: { id: string; tag_ids: string[] }): void
  (e: 'reject-description', payload: { id: string }): void
  (e: 'reject-tags', payload: { id: string }): void
}>()

const publishing = ref(false)
const isProcessing = computed(() => (props.isProcessing ?? false) || publishing.value)

const catalogStore = useCatalogStore()

// AI Suggestion handling
const editableSuggestion = ref(props.asset.ai_suggestion || '')
const editableSuggestedTags = ref<AssetTag[]>([])

// Watch for changes in AI suggestions
watch(
  () => props.asset.ai_suggestion,
  (newSuggestion) => {
    editableSuggestion.value = newSuggestion || ''
  }
)

// Initialize editable suggested tags (AI suggestions REPLACE existing tags)
watch(
  () => [props.asset.ai_suggested_tags, props.asset.tags, catalogStore.tagsArray.length] as const,
  ([suggestedTagNames]) => {
    if (suggestedTagNames && suggestedTagNames.length > 0) {
      const suggestedTags = suggestedTagNames
        .map((tagName) =>
          catalogStore.tagsArray.find((t) => t.name.toLowerCase() === tagName.toLowerCase())
        )
        .filter((tag): tag is AssetTag => tag !== undefined)

      // AI suggestions replace existing tags (not merge)
      editableSuggestedTags.value = suggestedTags
    } else {
      editableSuggestedTags.value = []
    }
  },
  { immediate: true }
)

// Computed: All suggested tags are shown as new (they replace existing tags)
const newSuggestedTags = computed(() => {
  if (!props.asset.ai_suggested_tags || props.asset.ai_suggested_tags.length === 0) return []

  // All suggested tags are new since AI suggestions replace existing tags
  return editableSuggestedTags.value
})

const iconByType: Record<AssetType, Component> = {
  DATABASE: Database,
  SCHEMA: FolderTree,
  TABLE: Database,
  COLUMN: Columns3
}

const columnOrigin = computed(() => {
  if (props.asset.type !== 'COLUMN') return ''

  const schema = props.asset.schema?.trim()
  const tableName = props.asset.tableName?.trim()

  if (schema && tableName) return `${schema}.${tableName}`
  if (tableName) return tableName
  if (schema) return schema

  return 'Unknown table'
})

const draft = reactive({
  description: '',
  tags: [] as AssetTag[]
})

// Initialize draft when asset changes
watch(
  () => props.asset,
  (asset) => {
    draft.description = asset.description || ''
    draft.tags = asset?.tags || []
  },
  { immediate: true }
)

const hasChanges = computed(() => {
  const descChanged = draft.description.trim() !== (props.asset.description || '').trim()
  const tagsChanged =
    draft.tags.length !== props.asset.tags.length ||
    draft.tags.some((tag, i) => tag.id !== props.asset.tags[i]?.id)

  return descChanged || tagsChanged
})

const hasAiSuggestions = computed(() => {
  return (
    !!props.asset.ai_suggestion ||
    (props.asset.ai_suggested_tags && props.asset.ai_suggested_tags.length > 0)
  )
})

function handleSave() {
  if (!hasChanges.value) return

  emit('save', {
    id: props.asset.id,
    description: draft.description.trim(),
    tag_ids: draft.tags.map((tag) => tag.id).filter((id) => id)
  })
}

function handleNavigateToCatalog() {
  emit('navigate-to-catalog', { id: props.asset.id })
}

async function handlePublish() {
  // Emit to parent to let it handle the publish action
  // This allows the parent to update its local state
  emit('publish', { id: props.asset.id })
}

function handleApproveDescription() {
  if (!editableSuggestion.value.trim()) return
  emit('approve-description', {
    id: props.asset.id,
    description: editableSuggestion.value.trim()
  })
}

function handleApproveTags() {
  const tagIds = editableSuggestedTags.value.map((tag) => tag.id).filter((id) => id)
  emit('approve-tags', {
    id: props.asset.id,
    tag_ids: tagIds
  })
}

function handleRejectDescription() {
  emit('reject-description', { id: props.asset.id })
}

function handleRejectTags() {
  emit('reject-tags', { id: props.asset.id })
}
</script>
