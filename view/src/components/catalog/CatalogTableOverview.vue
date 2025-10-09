<template>
  <div class="space-y-4">
    <div class="space-y-2">
      <div class="flex items-center justify-between gap-2">
        <h3 class="text-sm font-medium text-muted-foreground">Description</h3>
        <div v-if="asset && isEditing" class="flex items-center gap-2">
          <Button variant="ghost" size="sm" :disabled="isSaving" @click="$emit('cancel-edit')">
            Cancel
          </Button>
          <Button
            variant="outline"
            size="sm"
            :disabled="isSaving || !hasChanges"
            :is-loading="isSaving"
            @click="$emit('save')"
          >
            <template #loading>Saving...</template>
            Save
          </Button>
        </div>
      </div>
      <Textarea
        :model-value="draft.description"
        @update:model-value="updateDescription"
        rows="5"
        class="rounded-lg"
        :disabled="isSaving"
        @focus="$emit('start-edit')"
        placeholder="Click to add description..."
      />
      <p v-if="error" class="text-sm text-destructive">
        {{ error }}
      </p>
    </div>
    <div class="space-y-2">
      <h3 class="text-sm font-medium text-muted-foreground">Tags</h3>
      <AssetTagSelect
        :model-value="draft.tags"
        @update:model-value="updateTags"
        :disabled="isSaving"
        @focus="$emit('start-edit')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import AssetTagSelect from '@/components/AssetTagSelect.vue'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import type { AssetTag, CatalogAsset } from '@/stores/catalog'
import type { EditableDraft } from './types'

interface Props {
  asset: CatalogAsset
  draft: EditableDraft
  isEditing: boolean
  isSaving: boolean
  hasChanges: boolean
  error: string | null
  columnsCount: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'start-edit': []
  'cancel-edit': []
  save: []
  'update:draft': [draft: EditableDraft]
}>()

function updateDescription(description: string | number) {
  emit('update:draft', { ...props.draft, description: String(description) })
  emit('start-edit')
}

function updateTags(tags: AssetTag[]) {
  emit('update:draft', { ...props.draft, tags })
  emit('start-edit')
}
</script>
