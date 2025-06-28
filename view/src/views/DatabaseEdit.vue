<template>
  <div class="max-w-7xl mx-auto px-4">
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
    <!-- Action Buttons -->
    <div class="py-5 max-w-lg">
      <div class="flex justify-between space-x-3">
        <BaseButton
          :is-loading="isDeleting"
          @click="clickDelete"
          class="bg-red-400 text-white hover:bg-red-600"
        >
          Delete
        </BaseButton>
        <BaseButton :is-loading="isSaving" @click="clickSave"> Save </BaseButton>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BaseButton from '@/components/base/BaseButton.vue'
import DatabaseForm from '@/components/database/DatabaseForm.vue'
import router from '@/router'
import { useDatabasesStore } from '@/stores/databases'
import { ArrowLeftIcon } from '@heroicons/vue/24/solid'
import { notify } from 'notiwind'
import { ref } from 'vue'
import { useRoute } from 'vue-router'

const databaseForm = ref<InstanceType<typeof DatabaseForm> | null>(null)
const route = useRoute()
const databaseId = route.params.id as string
const isSaving = ref(false)
const isDeleting = ref(false)
const databasesStore = useDatabasesStore()

// Redirect to /databases
const clickCancel = () => {
  router.push({ name: 'DatabaseList' })
}

const clickDelete = async () => {
  isDeleting.value = true
  try {
    await databasesStore.deleteDatabase(databaseId)
    isDeleting.value = false
    router.push({ name: 'DatabaseList' })
  } catch (error) {
    console.error('Database delete failed:', error)
    notify({
      title: 'Database delete failed',
      text: error.response.data.error,
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
</script>
