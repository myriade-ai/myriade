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
import { useCatalogStore, type CatalogTerm } from '@/stores/catalog'
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
const showCreateTerm = ref(false)
const showDeleteDialog = ref(false)
const selectedTerm = ref<CatalogTerm | null>(null)
const editingTermId = ref<string | null>(null)

const newTerm = ref({
  name: '',
  definition: '',
  synonyms: '',
  businessDomains: ''
})

const editForm = ref<
  Record<string, { name: string; definition: string; synonyms: string; businessDomains: string }>
>({})

function startEditing(term: CatalogTerm) {
  editingTermId.value = term.id
  editForm.value[term.id] = {
    name: term.name,
    definition: term.definition,
    synonyms: term.synonyms ? term.synonyms.join(', ') : '',
    businessDomains: term.business_domains ? term.business_domains.join(', ') : ''
  }
}

function cancelEditing() {
  editingTermId.value = null
}

function isEditing(termId: string) {
  return editingTermId.value === termId
}

async function saveTerm(termId: string) {
  const formData = editForm.value[termId]
  if (!formData || !formData.name || !formData.definition) {
    return
  }

  try {
    const synonyms = formData.synonyms
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0)

    const domains = formData.businessDomains
      .split(',')
      .map((d) => d.trim())
      .filter((d) => d.length > 0)

    await catalogStore.updateTerm(termId, {
      name: formData.name,
      definition: formData.definition,
      synonyms: synonyms.length > 0 ? synonyms : undefined,
      business_domains: domains.length > 0 ? domains : undefined
    })

    editingTermId.value = null
  } catch (error) {
    console.error('Error updating term:', error)
  }
}

async function createTerm() {
  const databaseId = selectedDatabaseId.value
  if (!databaseId || !newTerm.value.name || !newTerm.value.definition) {
    return
  }

  try {
    const synonyms = newTerm.value.synonyms
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0)

    const domains = newTerm.value.businessDomains
      .split(',')
      .map((d) => d.trim())
      .filter((d) => d.length > 0)

    await catalogStore.createTerm(databaseId, {
      name: newTerm.value.name,
      definition: newTerm.value.definition,
      synonyms: synonyms.length > 0 ? synonyms : undefined,
      business_domains: domains.length > 0 ? domains : undefined
    })

    newTerm.value = { name: '', definition: '', synonyms: '', businessDomains: '' }
    showCreateTerm.value = false

    catalogStore.fetchTerms(databaseId)
  } catch (error) {
    console.error('Error creating term:', error)
  }
}

function openDeleteDialog(term: CatalogTerm) {
  selectedTerm.value = term
  showDeleteDialog.value = true
}

async function confirmDelete() {
  if (!selectedTerm.value) {
    return
  }

  try {
    await catalogStore.deleteTerm(selectedTerm.value.id)

    showDeleteDialog.value = false
    selectedTerm.value = null
  } catch (error) {
    console.error('Error deleting term:', error)
  }
}

watch(
  selectedDatabaseId,
  async (newDatabaseId, oldDatabaseId) => {
    if (!newDatabaseId || newDatabaseId === oldDatabaseId) {
      return
    }
    await catalogStore.fetchTerms(newDatabaseId)
  }
)

onMounted(async () => {
  if (selectedDatabaseId.value) {
    await catalogStore.fetchTerms(selectedDatabaseId.value)
  }
})
</script>
<template>
  <div>
    <PageHeader title="Catalog Terms" :subtitle="`${catalogStore.termsArray.length} terms`">
      <template #actions>
        <Button @click="showCreateTerm = true">
          <PlusIcon class="h-4 w-4" />
          Term
        </Button>
      </template>
    </PageHeader>
    <div class="px-4 py-4">
      <div v-if="catalogStore.termsArray.length > 0" class="space-y-4">
        <div
          v-for="term in catalogStore.termsArray"
          :key="term.id"
          class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div v-if="isEditing(term.id)" class="space-y-3">
            <div>
              <Label :for="`edit-name-${term.id}`">Name</Label>
              <Input
                :id="`edit-name-${term.id}`"
                v-model="editForm[term.id].name"
                required
                class="mt-1"
              />
            </div>
            <div>
              <Label :for="`edit-definition-${term.id}`">Definition</Label>
              <Textarea
                :id="`edit-definition-${term.id}`"
                v-model="editForm[term.id].definition"
                required
                class="mt-1"
                rows="3"
              />
            </div>
            <div>
              <Label :for="`edit-synonyms-${term.id}`">Synonyms (comma-separated)</Label>
              <Input
                :id="`edit-synonyms-${term.id}`"
                v-model="editForm[term.id].synonyms"
                class="mt-1"
              />
            </div>
            <div>
              <Label :for="`edit-domains-${term.id}`">Business Domains (comma-separated)</Label>
              <Input
                :id="`edit-domains-${term.id}`"
                v-model="editForm[term.id].businessDomains"
                class="mt-1"
              />
            </div>
            <div class="flex justify-end space-x-2">
              <Button @click="cancelEditing" variant="outline" size="sm"> Cancel </Button>
              <Button
                @click="saveTerm(term.id)"
                size="sm"
                :disabled="!editForm[term.id]?.name || !editForm[term.id]?.definition"
              >
                Save
              </Button>
            </div>
          </div>

          <div v-else class="flex items-start justify-between">
            <div class="flex-1 cursor-pointer" @click="startEditing(term)">
              <h3 class="text-lg font-medium text-gray-900">{{ term.name }}</h3>
              <p class="text-sm text-gray-600 mt-1">{{ term.definition }}</p>

              <div v-if="term.synonyms?.length" class="mt-2">
                <span class="text-xs text-gray-500">Synonyms: </span>
                <span class="text-xs text-gray-700">{{ term.synonyms.join(', ') }}</span>
              </div>

              <div v-if="term.business_domains?.length" class="mt-2 flex flex-wrap gap-1">
                <span
                  v-for="domain in term.business_domains"
                  :key="domain"
                  class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-purple-100 text-purple-800"
                >
                  {{ domain }}
                </span>
              </div>
            </div>

            <div class="flex items-center space-x-2 ml-4">
              <Button
                @click="openDeleteDialog(term)"
                variant="ghost"
                size="icon"
                class="h-8 w-8 text-red-600 hover:text-red-700 hover:bg-red-50"
                title="Delete term"
              >
                <Trash2 class="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-8">
        <p class="text-gray-500 mb-2">No business terms defined</p>
        <p class="text-sm text-gray-400 mb-4">
          Create terms to help define your business vocabulary
        </p>
        <Button @click="showCreateTerm = true"> Create Your First Term </Button>
      </div>
    </div>

    <Dialog v-model:open="showCreateTerm">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Business Term</DialogTitle>
        </DialogHeader>

        <form @submit.prevent="createTerm" class="space-y-4">
          <div>
            <Label for="termName">Name</Label>
            <Input id="termName" v-model="newTerm.name" required class="mt-1" />
          </div>

          <div>
            <Label for="termDefinition">Definition</Label>
            <Textarea
              id="termDefinition"
              v-model="newTerm.definition"
              required
              class="mt-1"
              rows="3"
            />
          </div>

          <div>
            <Label for="termSynonyms">Synonyms (comma-separated)</Label>
            <Input id="termSynonyms" v-model="newTerm.synonyms" class="mt-1" />
          </div>

          <div>
            <Label for="termDomains">Business Domains (comma-separated)</Label>
            <Input id="termDomains" v-model="newTerm.businessDomains" class="mt-1" />
          </div>

          <DialogFooter>
            <Button type="button" @click="showCreateTerm = false" variant="outline">
              Cancel
            </Button>
            <Button type="submit" :disabled="!newTerm.name || !newTerm.definition">
              Create Term
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

    <AlertDialog v-model:open="showDeleteDialog">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Term</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete the term "{{ selectedTerm?.name }}"? This action cannot
            be undone.
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
