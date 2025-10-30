<script setup lang="ts">
import PageHeader from '@/components/PageHeader.vue'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import Label from '@/components/ui/label/Label.vue'
import { Textarea } from '@/components/ui/textarea'
import { useCatalogStore, type AssetTag } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { PlusIcon, Trash2 } from 'lucide-vue-next'
import { computed, onMounted, ref, watch } from 'vue'

const contextsStore = useContextsStore()
const catalogStore = useCatalogStore()
const selectedDatabaseId = computed<string | null>(() => {
  try {
    return contextsStore.getSelectedContextDatabaseId()
  } catch (error) {
    return null
  }
})
const showCreateModal = ref(false)
const showDeleteDialog = ref(false)
const selectedTag = ref<AssetTag | null>(null)
const editingTagId = ref<string | null>(null)

const newTag = ref({
  name: '',
  description: ''
})

const editForm = ref<Record<string, { name: string; description: string }>>({})

function startEditing(tag: AssetTag) {
  editingTagId.value = tag.id
  editForm.value[tag.id] = {
    name: tag.name,
    description: tag.description || ''
  }
}

function cancelEditing() {
  editingTagId.value = null
}

function isEditing(tagId: string) {
  return editingTagId.value === tagId
}

async function createTag() {
  const databaseId = selectedDatabaseId.value
  if (!databaseId || !newTag.value.name) {
    return
  }

  try {
    await catalogStore.createTag(databaseId, {
      name: newTag.value.name,
      description: newTag.value.description || undefined
    })

    // Reset form
    newTag.value = { name: '', description: '' }
    showCreateModal.value = false

    catalogStore.fetchTags(databaseId)
  } catch (error) {
    console.error('Error creating tag:', error)
  }
}

async function saveTag(tagId: string) {
  const formData = editForm.value[tagId]
  if (!formData || !formData.name) {
    return
  }

  try {
    await catalogStore.updateTag(tagId, {
      name: formData.name,
      description: formData.description || undefined
    })

    editingTagId.value = null
  } catch (error) {
    console.error('Error updating tag:', error)
  }
}

function openDeleteDialog(tag: AssetTag) {
  selectedTag.value = tag
  showDeleteDialog.value = true
}

async function confirmDelete() {
  if (!selectedTag.value) {
    return
  }

  try {
    await catalogStore.deleteTag(selectedTag.value.id)

    showDeleteDialog.value = false
    selectedTag.value = null
  } catch (error) {
    console.error('Error deleting tag:', error)
  }
}

watch(
  selectedDatabaseId,
  async (newDatabaseId, oldDatabaseId) => {
    if (!newDatabaseId || newDatabaseId === oldDatabaseId) {
      return
    }
    await catalogStore.fetchTags(newDatabaseId)
  }
)

onMounted(async () => {
  if (selectedDatabaseId.value) {
    await catalogStore.fetchTags(selectedDatabaseId.value)
  }
})
</script>
<template>
  <div>
    <PageHeader title="Asset Tags" :subtitle="`${catalogStore.tagsArray.length} tags`">
      <template #actions>
        <Button @click="showCreateModal = true">
          <PlusIcon class="h-4 w-4" />
          Tag
        </Button>
      </template>
    </PageHeader>
    <div class="px-4 py-4">
      <div v-if="catalogStore.tagsArray.length > 0" class="space-y-4">
        <div
          v-for="tag in catalogStore.tagsArray"
          :key="tag.id"
          class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div v-if="isEditing(tag.id)" class="space-y-3">
            <div>
              <Label :for="`edit-name-${tag.id}`">Name</Label>
              <Input
                :id="`edit-name-${tag.id}`"
                v-model="editForm[tag.id].name"
                required
                class="mt-1"
              />
            </div>
            <div>
              <Label :for="`edit-description-${tag.id}`">Description (optional)</Label>
              <Textarea
                :id="`edit-description-${tag.id}`"
                v-model="editForm[tag.id].description"
                class="mt-1"
                rows="3"
              />
            </div>
            <div class="flex justify-end space-x-2">
              <Button @click="cancelEditing" variant="outline" size="sm"> Cancel </Button>
              <Button @click="saveTag(tag.id)" size="sm" :disabled="!editForm[tag.id]?.name">
                Save
              </Button>
            </div>
          </div>

          <!-- View Mode -->
          <div v-else class="flex items-start justify-between">
            <div class="flex-1 cursor-pointer" @click="startEditing(tag)">
              <h3 class="text-lg font-medium text-gray-900">{{ tag.name }}</h3>
              <p v-if="tag.description" class="text-sm text-gray-600 mt-1">
                {{ tag.description }}
              </p>
              <p v-else class="text-sm text-gray-400 italic mt-1">No description</p>
            </div>

            <div class="flex items-center space-x-2 ml-4">
              <Button
                @click="openDeleteDialog(tag)"
                variant="ghost"
                size="icon"
                class="h-8 w-8 text-red-600 hover:text-red-700 hover:bg-red-50"
                title="Delete tag"
              >
                <Trash2 class="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-8">
        <p class="text-gray-500 mb-2">No tags defined</p>
        <p class="text-sm text-gray-400 mb-4">Create tags to categorize your assets</p>
      </div>
    </div>

    <Dialog v-model:open="showCreateModal">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Tag</DialogTitle>
        </DialogHeader>

        <form @submit.prevent="createTag" class="space-y-4">
          <div>
            <Label for="tagName">Name</Label>
            <Input id="tagName" v-model="newTag.name" required class="mt-1" />
          </div>

          <div>
            <Label for="tagDescription">Description (optional)</Label>
            <Textarea id="tagDescription" v-model="newTag.description" class="mt-1" rows="3" />
          </div>

          <DialogFooter>
            <Button type="button" @click="showCreateModal = false" variant="outline">
              Cancel
            </Button>
            <Button type="submit" :disabled="!newTag.name"> Create Tag </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

    <AlertDialog v-model:open="showDeleteDialog">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Tag</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete the tag "{{ selectedTag?.name }}"? This will remove the
            tag from all assets. This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction @click="confirmDelete" variant="destructive">
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>
