<template>
  <div class="space-y-4">
    <div class="space-y-2">
      <div class="flex items-center justify-between gap-2">
        <h3 class="text-xs font-medium uppercase tracking-wide">Description</h3>
        <div
          v-if="asset && draft && !needsDescriptionReview && hasChanges"
          class="flex items-center gap-2"
        >
          <Button
            size="sm"
            class="h-7 text-xs"
            :disabled="isSaving"
            :is-loading="isSaving"
            @click="$emit('save')"
          >
            <template #loading>Saving...</template>
            Save
          </Button>
        </div>
      </div>

      <div v-if="needsDescriptionReview" class="space-y-3">
        <!-- Git-style unified diff view (only if there's an actual AI suggestion) -->
        <div v-if="asset.ai_suggestion" class="overflow-hidden rounded-lg border border-border">
          <div class="space-y-0 text-[13px] font-mono leading-relaxed">
            <!-- Before (removal) -->
            <div
              class="bg-red-50 dark:bg-red-950/30 px-3 py-2.5 border-l-[3px] border-red-400 dark:border-red-500 flex"
            >
              <span class="text-red-500 dark:text-red-400 select-none mr-2 flex-shrink-0">−</span>
              <span class="text-red-800 dark:text-red-200">{{
                asset.description || '(empty)'
              }}</span>
            </div>
            <!-- After (addition) - Editable -->
            <div
              class="bg-green-50 dark:bg-green-950/30 px-3 py-2.5 border-l-[3px] border-green-400 dark:border-green-500 flex"
            >
              <span class="text-green-500 dark:text-green-400 select-none mr-2 flex-shrink-0"
                >+</span
              >
              <Textarea
                :model-value="editableSuggestion"
                @update:model-value="updateEditableSuggestion"
                rows="3"
                class="flex-1 border-0 p-0 text-[13px] font-mono text-green-800 dark:text-green-200 bg-transparent focus:ring-0 focus:ring-offset-0 focus:outline-none focus:border-0 focus-visible:ring-0 focus-visible:ring-offset-0 resize-none leading-relaxed shadow-none"
                :disabled="isSaving"
                placeholder="Edit AI suggestion..."
              />
            </div>
          </div>
          <!-- Action buttons for description -->
          <div class="px-3 py-2.5 bg-muted/30 border-t border-border flex justify-end gap-2">
            <Button
              @click="handleRejectDescription"
              size="sm"
              variant="ghost"
              class="h-7 text-xs"
              :disabled="isSaving"
            >
              Reject
            </Button>
            <Button
              @click="handleApproveDescription"
              size="sm"
              class="h-7 text-xs"
              :disabled="isSaving || !editableSuggestion.trim()"
              :is-loading="isSaving"
            >
              <template #loading>Accepting...</template>
              Accept changes
            </Button>
          </div>
        </div>

        <!-- If no AI suggestion, just show editable textarea -->
        <Textarea
          v-else
          :model-value="editableSuggestion"
          @update:model-value="updateEditableSuggestion"
          rows="5"
          class="rounded-lg text-sm"
          :disabled="isSaving"
          placeholder="Edit description..."
        />
      </div>

      <!-- Regular description view/edit (all other statuses) -->
      <div v-else>
        <MarkdownEditor
          :model-value="draft.description"
          @update:model-value="updateDescription"
          @submit="$emit('save')"
          :disabled="isSaving"
          :show-bubble-menu="false"
          placeholder="Enter asset description..."
          min-height="80px"
          :compact="true"
          class="rounded-lg border border-border bg-transparent hover:border-border/80 focus-within:border-primary/50 transition-colors"
        />
      </div>

      <p v-if="error" class="text-sm text-destructive">
        {{ error }}
      </p>
    </div>

    <!-- Tags Section with diff (only in needsReview mode and if there are suggested tags) -->
    <div v-if="needsReview && asset.ai_suggested_tags && asset.ai_suggested_tags.length > 0">
      <h3 class="text-xs font-medium uppercase tracking-wide mb-2">Tags</h3>

      <!-- Git-style unified diff view for tags -->
      <div class="overflow-hidden rounded-lg border border-border">
        <div class="space-y-0">
          <!-- Before (removal) - Current tags -->
          <div
            class="bg-red-50 dark:bg-red-950/30 px-3 py-2.5 border-l-[3px] border-red-400 dark:border-red-500 flex items-center gap-2 flex-wrap"
          >
            <span class="text-red-500 dark:text-red-400 select-none text-sm">−</span>
            <div v-if="asset.tags.length > 0" class="flex items-center gap-1.5 flex-wrap">
              <Badge
                v-for="tag in asset.tags"
                :key="tag.id"
                variant="outline"
                class="text-red-700 dark:text-red-300 border-red-200 dark:border-red-800 bg-transparent text-xs"
              >
                {{ tag.name }}
              </Badge>
            </div>
            <span v-else class="text-red-600 dark:text-red-400 text-xs italic">No tags</span>
          </div>
          <!-- After (addition) - Show only NEW suggested tags in diff -->
          <div
            v-if="newSuggestedTagsForDiff.length > 0"
            class="bg-green-50 dark:bg-green-950/30 px-3 py-2.5 border-l-[3px] border-green-400 dark:border-green-500 flex items-center gap-2 flex-wrap"
          >
            <span class="text-green-500 dark:text-green-400 select-none text-sm">+</span>
            <div class="flex items-center gap-1.5 flex-wrap">
              <Badge
                v-for="tag in newSuggestedTagsForDiff"
                :key="tag.id"
                variant="outline"
                class="text-green-700 dark:text-green-300 border-green-200 dark:border-green-800 bg-transparent text-xs"
              >
                {{ tag.name }}
              </Badge>
            </div>
          </div>
          <!-- Edit all tags section (shown separately) -->
          <div class="px-3 py-2.5 border-t border-border">
            <label class="text-[11px] font-medium uppercase tracking-wide mb-2 block"
              >Edit Tags</label
            >
            <AssetTagSelect
              v-model="editableSuggestedTags"
              :disabled="isSaving"
              class="bg-transparent border-0"
            />
          </div>
          <!-- Action buttons for tags -->
          <div class="px-3 py-2.5 bg-muted/30 border-t border-border flex justify-end gap-2">
            <Button
              @click="handleRejectTags"
              size="sm"
              variant="ghost"
              class="h-7 text-xs"
              :disabled="isSaving"
            >
              Reject
            </Button>
            <Button
              @click="handleApproveTags"
              size="sm"
              class="h-7 text-xs"
              :disabled="isSaving"
              :is-loading="isSaving"
            >
              <template #loading>Accepting...</template>
              Accept changes
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Regular tags section (when not in needsReview mode or no suggested tags) -->
    <div v-else class="space-y-2">
      <h3 class="text-xs font-medium uppercase tracking-wide">Tags</h3>
      <AssetTagSelect
        :model-value="draft.tags"
        @update:model-value="updateTags"
        class="w-full flex-1"
        :disabled="isSaving"
        @focus="$emit('start-edit')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import AssetTagSelect from '@/components/AssetTagSelect.vue'
import MarkdownEditor from '@/components/MarkdownEditor.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useCatalogStore, type AssetTag, type CatalogAsset } from '@/stores/catalog'
import { computed, ref, watch } from 'vue'
import type { EditableDraft } from './types'

interface Props {
  asset: CatalogAsset
  draft: EditableDraft
  isEditing: boolean
  isSaving: boolean
  hasChanges: boolean
  error: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'start-edit': []
  'cancel-edit': []
  save: []
  'update:draft': [draft: EditableDraft]
  'approve-description': [description: string]
  'approve-tags': [tagIds: string[]]
  'reject-description': []
  'reject-tags': []
}>()

const catalogStore = useCatalogStore()

const needsReview = computed(() => {
  // Only show approve workflow if there's an actual AI suggestion or suggested tags
  return Boolean(props.asset.ai_suggestion || props.asset.ai_suggested_tags)
})

const needsDescriptionReview = computed(() => {
  // Only show description approve workflow if there's an actual AI suggestion
  return Boolean(props.asset.ai_suggestion)
})

const editableSuggestion = ref(
  props.asset.ai_suggestion || (needsReview.value ? props.asset.description || '' : '')
)

// Convert suggested tag names to AssetTag objects by looking up existing tags
// AI suggestions REPLACE existing tags (not merge)
function initializeEditableSuggestedTags(): AssetTag[] {
  if (props.asset.ai_suggested_tags && needsReview.value) {
    const suggestedTags = props.asset.ai_suggested_tags
      .map((tagName) =>
        catalogStore.tagsArray.find((t) => t.name.toLowerCase() === tagName.toLowerCase())
      )
      .filter((tag): tag is AssetTag => tag !== undefined)

    // Return only suggested tags - they replace existing tags
    return suggestedTags
  }
  return []
}

const editableSuggestedTags = ref<AssetTag[]>(initializeEditableSuggestedTags())

// Computed: All suggested tags are shown as new (they replace existing tags)
const newSuggestedTagsForDiff = computed(() => {
  if (!needsReview.value || !props.asset.ai_suggested_tags) return []

  // All suggested tags are new since AI suggestions replace existing tags
  return editableSuggestedTags.value
})

watch(
  () => [props.asset.ai_suggestion, props.asset.description, props.asset.status] as const,
  ([newSuggestion, newDescription, newStatus]) => {
    const isReviewStatus = newStatus === 'draft'
    editableSuggestion.value = newSuggestion || (isReviewStatus ? newDescription || '' : '')
  }
)

watch(
  () =>
    [
      props.asset.ai_suggested_tags,
      props.asset.status,
      props.asset.tags,
      catalogStore.tagsArray.length
    ] as const,
  ([newSuggestedTags, newStatus]) => {
    const isReviewStatus = newStatus === 'draft'
    if (newSuggestedTags && isReviewStatus) {
      const suggestedTags = newSuggestedTags
        .map((tagName) =>
          catalogStore.tagsArray.find((t) => t.name.toLowerCase() === tagName.toLowerCase())
        )
        .filter((tag): tag is AssetTag => tag !== undefined)

      // AI suggestions replace existing tags (not merge)
      editableSuggestedTags.value = suggestedTags
    } else {
      editableSuggestedTags.value = []
    }
  }
)

function updateDescription(description: string) {
  emit('update:draft', { ...props.draft, description })
}

function updateTags(tags: AssetTag[]) {
  emit('update:draft', { ...props.draft, tags })
  emit('start-edit')
}

function updateEditableSuggestion(value: string | number) {
  editableSuggestion.value = String(value)
}

function handleApproveDescription() {
  if (!editableSuggestion.value.trim()) return
  emit('approve-description', editableSuggestion.value.trim())
}

function handleApproveTags() {
  const tagIds = editableSuggestedTags.value
    .map((tag: AssetTag) => tag.id)
    .filter((id: string) => id) // Filter out empty IDs
  emit('approve-tags', tagIds)
}

function handleRejectDescription() {
  emit('reject-description')
}

function handleRejectTags() {
  emit('reject-tags')
}
</script>
