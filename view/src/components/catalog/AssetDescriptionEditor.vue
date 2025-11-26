<template>
  <div class="space-y-4">
    <div class="space-y-2">
      <div class="flex items-center justify-between gap-2">
        <h3 class="text-sm font-medium text-muted-foreground">Description</h3>
        <div
          v-if="asset && draft && isEditing && !needsDescriptionReview"
          class="flex items-center gap-2"
        >
          <Button variant="ghost" size="sm" :disabled="isSaving" @click="$emit('cancel-edit')">
            Cancel
          </Button>
          <Transition
            enter-active-class="transition-opacity duration-200"
            leave-active-class="transition-opacity duration-200"
            enter-from-class="opacity-0"
            leave-to-class="opacity-0"
          >
            <Button
              v-if="hasChanges"
              variant="outline"
              size="sm"
              :disabled="isSaving || !hasChanges"
              :is-loading="isSaving"
              @click="$emit('save')"
            >
              <template #loading>Saving...</template>
              Save
            </Button>
          </Transition>
        </div>
      </div>

      <div v-if="needsDescriptionReview" class="space-y-3">
        <!-- Git-style unified diff view (only if there's an actual AI suggestion) -->
        <div v-if="asset.ai_suggestion" class="overflow-hidden bg-card border rounded-md">
          <div class="space-y-0 text-xs font-mono leading-relaxed">
            <!-- Before (removal) -->
            <div class="bg-red-50 dark:bg-red-900/20 px-2 py-1 border-l-2 border-red-400">
              <span class="text-red-600 select-none mr-2">−</span>
              <span class="text-red-900 dark:text-red-200">{{ asset.description || '' }}</span>
            </div>
            <!-- After (addition) - Editable -->
            <div class="bg-green-50 dark:bg-green-900/20 px-2 py-1 border-l-2 border-green-400">
              <span class="text-green-600 select-none mr-2">+</span>
              <Textarea
                :model-value="editableSuggestion"
                @update:model-value="updateEditableSuggestion"
                rows="3"
                class="inline-block align-top w-[calc(100%-1.5rem)] border-0 p-0 text-xs font-mono text-green-900 dark:text-green-200 bg-transparent focus:ring-0 focus:ring-offset-0 focus:outline-none focus:border-0 focus-visible:ring-0 focus-visible:ring-offset-0 resize-none leading-relaxed shadow-none"
                :disabled="isSaving"
                placeholder="Edit AI suggestion..."
              />
            </div>
          </div>
          <!-- Action buttons for description -->
          <div class="px-2 py-2 bg-gray-50 border-t flex justify-end gap-2">
            <Button @click="handleRejectDescription" size="sm" variant="ghost" :disabled="isSaving">
              Reject
            </Button>
            <Button
              @click="handleApproveDescription"
              size="sm"
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
          class="rounded-lg"
          :disabled="isSaving"
          placeholder="Edit description..."
        />
      </div>

      <!-- Regular description view/edit (all other statuses) -->
      <div v-else>
        <!-- Read-only markdown view when not editing -->
        <div
          v-if="!isEditing && draft.description"
          class="prose prose-sm max-w-none p-3 rounded-lg border border-border bg-muted/30 cursor-pointer hover:bg-muted transition-colors"
          @click="$emit('start-edit')"
        >
          <MarkdownDisplay :content="draft.description" class="text-sm" />
        </div>
        <!-- Editable textarea when editing or no description -->
        <Textarea
          v-else
          :model-value="draft.description"
          @update:model-value="updateDescription"
          rows="5"
          class="rounded-lg"
          :disabled="isSaving"
          @focus="$emit('start-edit')"
          placeholder="Click to add description..."
        />
      </div>

      <p v-if="error" class="text-sm text-destructive">
        {{ error }}
      </p>
    </div>

    <!-- Tags Section with diff (only in needsReview mode and if there are suggested tags) -->
    <div v-if="needsReview && asset.ai_suggested_tags && asset.ai_suggested_tags.length > 0">
      <h3 class="text-sm font-medium text-muted-foreground">Tags</h3>

      <!-- Git-style unified diff view for tags -->
      <div class="overflow-hidden bg-card border rounded-md">
        <div class="space-y-0">
          <!-- Before (removal) - Current tags -->
          <div class="bg-red-50 dark:bg-red-900/20 px-3 py-2 border-l-2 border-red-400">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-red-600 select-none">−</span>
              <div v-if="asset.tags.length > 0" class="flex items-center gap-1 flex-wrap">
                <Badge
                  v-for="tag in asset.tags"
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
            v-if="newSuggestedTagsForDiff.length > 0"
            class="bg-green-50 dark:bg-green-900/20 px-3 py-2 border-l-2 border-green-400"
          >
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-green-600 select-none">+</span>
              <div class="flex items-center gap-1 flex-wrap">
                <Badge
                  v-for="tag in newSuggestedTagsForDiff"
                  :key="tag.id"
                  variant="outline"
                  class="text-green-900 dark:text-green-200 border-green-200"
                >
                  {{ tag.name }}
                </Badge>
              </div>
            </div>
          </div>
          <!-- Edit all tags section (shown separately) -->
          <div class="px-3 py-2 border-t border-gray-200">
            <label class="text-xs font-medium text-muted-foreground mb-2 block">Edit Tags</label>
            <AssetTagSelect
              v-model="editableSuggestedTags"
              :disabled="isSaving"
              class="bg-transparent border-0"
            />
          </div>
          <!-- Action buttons for tags -->
          <div class="px-3 py-2 bg-gray-50 border-t flex justify-end gap-2">
            <Button @click="handleRejectTags" size="sm" variant="ghost" :disabled="isSaving">
              Reject
            </Button>
            <Button
              @click="handleApproveTags"
              size="sm"
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
    <div v-else class="space-y-2 w-full flex-1">
      <h3 class="text-sm font-medium text-muted-foreground">Tags</h3>
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
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useCatalogStore, type AssetTag, type CatalogAsset } from '@/stores/catalog'
import { Info } from 'lucide-vue-next'
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

function updateDescription(description: string | number) {
  emit('update:draft', { ...props.draft, description: String(description) })
  emit('start-edit')
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
