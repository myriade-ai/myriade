<template>
  <div>
    <PageHeader title="Database" subtitle="Manage your database connections and options." />
    <div class="mx-auto px-4">
      <nav class="flex items-center justify-between px-4 sm:px-0">
        <div class="-mt-px flex w-0 flex-1">
          <a
            @click.prevent="clickCancel"
            class="inline-flex items-center border-t-2 border-transparent pt-4 pr-1 text-sm font-medium text-gray-500 hover:text-gray-700 cursor-pointer"
          >
            <ArrowLeftIcon class="mr-3 h-5 w-5 text-gray-400" aria-hidden="true" />
            Return to all databases
          </a>
        </div>
      </nav>
      <br />

      <DatabaseForm
        ref="databaseForm"
        mode="edit"
        :database-id="databaseId"
        @saved="onSaved"
        @error="onError"
      />

      <!-- Organisation Sharing Section -->
      <div v-if="canManageSharing" class="py-5 max-w-lg">
        <div class="p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h3 class="text-sm font-medium text-gray-900 mb-2">Organisation Sharing</h3>
          <p class="text-sm text-gray-500 mb-4">
            Share this database with your organisation to allow other members to access it.
          </p>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-700">
              {{ isSharedWithOrg ? 'Shared with organisation' : 'Private (only you)' }}
            </span>
            <Button
              :is-loading="isSharingToggling"
              @click="toggleSharing"
              :variant="isSharedWithOrg ? 'outline' : 'default'"
              size="sm"
            >
              {{ isSharedWithOrg ? 'Unshare' : 'Share to Organisation' }}
            </Button>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="py-5 max-w-lg">
        <div class="flex justify-between space-x-3">
          <Button :is-loading="isDeleting" @click="showDeleteDialog = true" variant="destructive">
            Delete
          </Button>
          <Button :is-loading="isSaving" @click="clickSave"> Save </Button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Dialog -->
    <AlertDialog :open="showDeleteDialog" @update:open="showDeleteDialog = $event">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Database Connection?</AlertDialogTitle>
          <AlertDialogDescription>
            <p class="mb-4">
              This action cannot be undone. Deleting this database will permanently remove:
            </p>
            <ul class="list-disc list-inside space-y-2 text-sm text-gray-700 mb-4">
              <li>All conversations and chat history</li>
              <li>All saved queries and charts</li>
              <li>All projects and their configurations</li>
              <li>All catalog metadata (assets, tags, terms)</li>
              <li>All data quality issues and business entities</li>
              <li>All documents and documentation</li>
              <li>All DBT configurations</li>
              <li>All GitHub integrations</li>
            </ul>
            <p class="text-sm font-medium text-red-600">
              Are you sure you want to permanently delete "{{ database?.name }}"?
            </p>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            @click="confirmDelete"
            class="bg-red-600 hover:bg-red-700 focus:ring-red-600"
          >
            Delete Permanently
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>

<script setup lang="ts">
import DatabaseForm from '@/components/database/DatabaseForm.vue'
import PageHeader from '@/components/PageHeader.vue'
import { Button } from '@/components/ui/button'
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
import router from '@/router'
import { user } from '@/stores/auth'
import { useDatabasesStore, type Database } from '@/stores/databases'
import { ArrowLeftIcon } from '@heroicons/vue/24/solid'
import { notify } from 'notiwind'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

const databaseForm = ref<InstanceType<typeof DatabaseForm> | null>(null)
const route = useRoute()
const databaseId = route.params.id as string
const isSaving = ref(false)
const isDeleting = ref(false)
const isSharingToggling = ref(false)
const showDeleteDialog = ref(false)
const databasesStore = useDatabasesStore()
const database = ref<Database | null>(null)

// Fetch database details
onMounted(async () => {
  try {
    database.value = await databasesStore.getDatabaseById(databaseId)
  } catch (error) {
    console.error('Failed to load database:', error)
  }
})

// Computed properties for sharing
const canManageSharing = computed(() => {
  return user.value.inOrganization && database.value && database.value.ownerId === user.value.id
})

const isSharedWithOrg = computed(() => {
  return database.value?.organisationId !== null && database.value?.organisationId !== undefined
})

// Redirect to /databases
const clickCancel = () => {
  router.push({ name: 'DatabaseList' })
}

const confirmDelete = async () => {
  showDeleteDialog.value = false
  isDeleting.value = true
  try {
    await databasesStore.deleteDatabase(databaseId)
    notify({
      title: 'Database deleted',
      text: 'The database and all related data have been permanently deleted',
      type: 'success'
    })
    isDeleting.value = false
    router.push({ name: 'DatabaseList' })
  } catch (error: any) {
    console.error('Database delete failed:', error)
    notify({
      title: 'Database delete failed',
      text: error.response?.data?.error || 'An error occurred while deleting the database',
      type: 'error'
    })
    isDeleting.value = false
  }
}

const clickSave = async () => {
  if (!databaseForm.value) return
  isSaving.value = true
  await databaseForm.value.save()
}
const onError = () => {
  isSaving.value = false
}

const onSaved = () => {
  router.push({ name: 'DatabaseList' })
}

const toggleSharing = async () => {
  if (!database.value) return

  isSharingToggling.value = true
  try {
    const shareToOrg = !isSharedWithOrg.value
    const updatedDatabase = await databasesStore.shareDatabaseToOrganisation(databaseId, shareToOrg)
    database.value = updatedDatabase

    notify({
      title: shareToOrg ? 'Shared with organisation' : 'Unshared from organisation',
      text: shareToOrg
        ? 'Database is now accessible to your organisation members'
        : 'Database is now private',
      type: 'success'
    })
  } catch (error: any) {
    console.error('Failed to toggle sharing:', error)
    notify({
      title: 'Failed to update sharing',
      text: error.response?.data?.error || 'An error occurred',
      type: 'error'
    })
  } finally {
    isSharingToggling.value = false
  }
}
</script>
