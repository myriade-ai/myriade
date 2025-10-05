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
        <component :is="iconByType[internalAsset.type]" class="w-5 h-5" />
        <span>{{ internalAsset.name }}</span>
      </CardTitle>
      <CardDescription class="flex flex-wrap items-center gap-1">
        <Badge
          :class="
            cn(
              internalAsset.type === 'TABLE'
                ? 'bg-blue-100 text-blue-800'
                : 'bg-green-100 text-green-800'
            )
          "
          >{{ internalAsset.type }}</Badge
        >

        <p v-if="internalAsset.type === 'COLUMN'" class="text-sm text-muted-foreground">
          from {{ columnOrigin }}
        </p>
        <p v-else-if="internalAsset.type === 'TABLE'" class="text-sm text-muted-foreground">
          from {{ internalAsset.schema }}
        </p>
      </CardDescription>
      <CardAction class="flex flex-wrap items-center justify-end gap-2">
        <template v-if="showEditToggle">
          <template v-if="isEditing">
            <Button
              variant="link"
              size="sm"
              :disabled="saving || isProcessing"
              @click="handleCancelEdit"
            >
              Cancel
            </Button>
            <Button
              variant="link"
              class="text-green-600 p-0"
              size="sm"
              :disabled="saving || isProcessing || !hasChanges"
              :is-loading="saving"
              @click="handleSave"
            >
              <template #loading>Saving...</template>
              Save & approve
            </Button>
          </template>
          <Button
            v-else
            variant="link"
            size="sm"
            class="p-0"
            :disabled="saving || isProcessing"
            @click="toggleEditMode"
          >
            Edit
          </Button>
        </template>
        <Button
          v-if="showApproveButton"
          variant="link"
          size="sm"
          :disabled="isProcessing"
          :is-loading="isProcessing"
          @click="handleApprove"
          class="text-green-600 p-0"
        >
          <template #loading>Approving...</template>
          Approve
        </Button>
        <Button
          v-if="showCatalogShortcut"
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
      <TooltipProvider :disabled="!internalAsset.description" v-if="!isEditing">
        <Tooltip>
          <TooltipTrigger>
            <p class="text-sm text-muted-foreground whitespace-pre-line line-clamp-3 text-start">
              {{ internalAsset.description || 'No description available.' }}
            </p>
          </TooltipTrigger>
          <TooltipContent class="max-w-xs whitespace-pre-line" side="right">
            <p>{{ internalAsset.description || 'No description available.' }}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
      <Textarea
        v-else
        v-model="draft.description"
        rows="4"
        class="max-h-72"
        :disabled="isProcessing || saving"
      />
    </CardContent>
    <CardFooter class="flex flex-col gap-2 items-start">
      <Badge
        v-if="internalAsset.type === 'COLUMN' && hasPrivacyConfiguration"
        :class="cn('flex items-center gap-1 bg-amber-100 text-amber-800')"
      >
        <Shield class="w-3 h-3" />
        Encrypted
      </Badge>
      <div v-if="!isEditing" class="flex flex-wrap gap-1">
        <Badge v-for="tag in internalAsset.tags" :key="tag.id">
          {{ tag.name }}
        </Badge>
        <p v-if="!internalAsset.tags?.length" class="text-sm text-muted-foreground">No tags yet.</p>
      </div>

      <AssetTagSelect
        v-else
        v-model="draft.tags"
        :disabled="isProcessing || saving"
        class="w-full"
      />
    </CardFooter>
  </Card>
</template>

<script lang="ts" setup>
import { cn } from '@/lib/utils'
import { useCatalogStore, type AssetTag, type AssetType, type Privacy } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { Columns3, Database, ExternalLink, Shield } from 'lucide-vue-next'
import { computed, reactive, ref, watch, type Component } from 'vue'
import AssetTagSelect from './AssetTagSelect.vue'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle
} from './ui/card'
import { Textarea } from './ui/textarea'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip'

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
  reviewed?: boolean
}

const props = defineProps<{
  asset: AssetInput
  mode?: 'catalog' | 'approval'
  disableEditing?: boolean
  isProcessing?: boolean
  showApprove?: boolean
  selected?: boolean
}>()

const emit = defineEmits<{
  (e: 'approve', payload: { id: string; description: string; tag_ids: string[] }): void
  (e: 'navigate-to-catalog', payload: { id: string }): void
}>()

const catalogStore = useCatalogStore()
const contextsStore = useContextsStore()

const approving = ref(false)

const isProcessing = computed(() => (props.isProcessing ?? false) || approving.value)
const isApprovalMode = computed(() => props.mode === 'approval')
const showApproveButton = computed(() => {
  if (isApprovalMode.value) {
    return props.showApprove !== false
  }

  if (isEditing.value) {
    return false
  }

  const hasNoValues =
    internalAsset.value.description?.length === 0 && internalAsset.value.tags?.length === 0

  if (hasNoValues) {
    return false
  }

  return internalAsset.value.reviewed === false
})

const showCatalogShortcut = computed(() => showApproveButton.value && props.mode !== 'catalog')

const iconByType: Record<AssetType, Component> = {
  TABLE: Database,
  COLUMN: Columns3
}

const saving = ref(false)

const internalAsset = ref<AssetInput>({
  id: props.asset.id,
  type: props.asset.type,
  name: props.asset.name,
  description: props.asset.description ?? '',
  tags: props.asset.tags ? [...props.asset.tags] : [],
  schema: props.asset.schema,
  tableName: props.asset.tableName,
  dataType: props.asset.dataType,
  privacy: props.asset.privacy,
  reviewed: props.asset.reviewed ?? false
})

const columnOrigin = computed(() => {
  if (internalAsset.value.type !== 'COLUMN') return ''

  const schema = internalAsset.value.schema?.trim()
  const tableName = internalAsset.value.tableName?.trim()

  if (schema && tableName) return `${schema}.${tableName}`
  if (tableName) return tableName
  if (schema) return schema

  return 'Unknown table'
})

const hasPrivacyConfiguration = computed(() => {
  if (internalAsset.value.type !== 'COLUMN') {
    return false
  }

  const privacyConfig = internalAsset.value.privacy?.llm ?? 'Default'

  return privacyConfig !== 'Default'
})

const draft = reactive({
  description: internalAsset.value.description ?? '',
  tags: [...internalAsset.value.tags]
})

watch(
  () => props.asset,
  (newAsset) => {
    internalAsset.value = {
      id: newAsset.id,
      type: newAsset.type,
      name: newAsset.name,
      description: newAsset.description ?? '',
      tags: newAsset.tags ? [...newAsset.tags] : [],
      schema: newAsset.schema,
      tableName: newAsset.tableName,
      dataType: newAsset.dataType,
      privacy: newAsset.privacy,
      reviewed: newAsset.reviewed ?? false
    }
    syncDraftFromAsset()
  },
  { immediate: true, deep: true }
)

const editMode = ref(false)

watch(
  () => props.mode,
  (mode) => {
    editMode.value = mode === 'approval'
  },
  { immediate: true }
)

const showEditToggle = computed(() => !isApprovalMode.value && !props.disableEditing)
const isEditing = computed(() => editMode.value && !props.disableEditing)

const normalizedCurrentTags = computed(() => normalizeTagIds(internalAsset.value.tags))
const normalizedDraftTags = computed(() => normalizeTagIds(draft.tags))
const hasChanges = computed(() => {
  const descriptionChanged =
    (draft.description ?? '').trim() !== (internalAsset.value.description ?? '').trim()
  if (descriptionChanged) return true

  if (normalizedCurrentTags.value.length !== normalizedDraftTags.value.length) {
    return true
  }
  return normalizedCurrentTags.value.some(
    (tagId, index) => tagId !== normalizedDraftTags.value[index]
  )
})

function normalizeTagIds(tags: AssetTag[]) {
  const seen = new Set<string>()
  const normalized: string[] = []
  tags.forEach((tag) => {
    if (tag.id && !seen.has(tag.id)) {
      seen.add(tag.id)
      normalized.push(tag.id)
    }
  })
  return normalized
}

function syncDraftFromAsset() {
  draft.description = internalAsset.value.description ?? ''
  draft.tags = [...internalAsset.value.tags]
}

function toggleEditMode() {
  editMode.value = true
}

function handleCancelEdit() {
  syncDraftFromAsset()
  editMode.value = false
}

function buildPayload() {
  return {
    id: internalAsset.value.id,
    description: draft.description.trim(),
    tag_ids: draft.tags.map((tag) => tag.id)
  }
}

async function handleSave() {
  if (isApprovalMode.value) {
    return
  }

  const contextId = contextsStore.contextSelected?.id
  if (!contextId) {
    console.warn('Cannot update asset without an active context')
    return
  }

  if (!hasChanges.value) {
    editMode.value = false
    return
  }

  const payload = buildPayload()

  try {
    saving.value = true
    const updated = await catalogStore.updateAsset(payload.id, {
      description: payload.description,
      tag_ids: payload.tag_ids
    })
    internalAsset.value = {
      ...internalAsset.value,
      description: updated.description ?? payload.description,
      tags: updated.tags
    }
    syncDraftFromAsset()
    editMode.value = false
  } catch (error) {
    console.error('Failed to update asset', error)
  } finally {
    saving.value = false
  }
}

async function handleApprove() {
  const payload = buildPayload()

  if (isApprovalMode.value) {
    emit('approve', payload)
    return
  }

  const contextId = contextsStore.contextSelected?.id
  if (!contextId) {
    console.warn('Cannot approve asset without an active context')
    return
  }

  try {
    approving.value = true
    const updated = await catalogStore.updateAsset(payload.id, {
      description: payload.description,
      tag_ids: payload.tag_ids,
      reviewed: true
    })

    internalAsset.value = {
      ...internalAsset.value,
      description: updated.description ?? payload.description,
      tags: updated.tags,
      reviewed: updated.reviewed ?? true
    }
    syncDraftFromAsset()
    editMode.value = false
  } catch (error) {
    console.error('Failed to mark asset as reviewed', error)
  } finally {
    approving.value = false
  }
}

function handleNavigateToCatalog() {
  const targetId = internalAsset.value.id
  if (!targetId) return
  emit('navigate-to-catalog', { id: targetId })
}
</script>
