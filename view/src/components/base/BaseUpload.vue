<template>
  <div @click="handleClick" @drop.prevent="uploadFileHandle" v-if="upload.status === null">
    <div
      class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md"
    >
      <div class="space-y-1 text-center">
        <CloudArrowUpIcon class="mx-auto h-12 w-12 text-gray-400" aria-hidden="true" />
        <div class="flex text-sm text-gray-600">
          <label
            for="file-upload"
            class="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-hidden focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
          >
            <span id="upload-text">Upload a file</span>
            <input
              ref="fileUploadInput"
              id="file-upload"
              name="file-upload"
              type="file"
              class="sr-only"
              accept=".csv"
              @change="uploadFileHandle"
            />
          </label>
          <p class="pl-1">or drag and drop</p>
        </div>
        <p class="text-xs text-gray-500">(.csv)</p>
      </div>
    </div>
  </div>

  <BaseNotification
    v-if="upload.status === STATUS.inProgress"
    :title="`Uploading ${upload.name}... (${upload.progress}%)`"
    :progress="upload.progress"
  ></BaseNotification>
  <BaseNotification
    v-if="upload.status === STATUS.done"
    color="green"
    :title="`Uploaded ${upload.name}.`"
    :message="upload.message"
    :display-close="true"
    @close="resetUpload"
  ></BaseNotification>
  <BaseNotification
    v-if="upload.status === STATUS.stopped"
    color="red"
    :title="`Error uploading ${upload.name}`"
    :message="upload.message"
    :display-close="true"
    @close="resetUpload"
  ></BaseNotification>
</template>

<script setup lang="ts">
import { CloudArrowUpIcon } from '@heroicons/vue/24/solid'

import BaseNotification from '@/components/base/BaseNotification.vue'
import { useDatabasesStore } from '@/stores/databases'
import { onMounted, onUnmounted, ref } from 'vue'

const { fetchDatabases } = useDatabasesStore()

const STATUS = {
  done: 'DONE',
  inProgress: 'IN_PROGRESS',
  stopped: 'STOPPED'
}

const fileUploadInput = ref(null)

const defaultUpload = {
  status: null,
  name: null,
  progress: null,
  message: null
}
const upload = ref({ ...defaultUpload })

const resetUpload = () => {
  upload.value = { ...defaultUpload }
}

function preventDefaults(e) {
  e.preventDefault()
}

const events = ['dragenter', 'dragover', 'dragleave', 'drop']

onMounted(() => {
  events.forEach((eventName) => {
    document.body.addEventListener(eventName, preventDefaults)
  })
})

onUnmounted(() => {
  events.forEach((eventName) => {
    document.body.removeEventListener(eventName, preventDefaults)
  })
})

const handleClick = async (event) => {
  if (event.pointerType === 'mouse' && event.target.id != 'upload-text') {
    fileUploadInput.value.click()
  }
}

// upload file
const uploadFile = async (file: File) => {
  upload.value.status = STATUS.inProgress
  upload.value.name = file.name

  const formData = new FormData()
  formData.append('file', file)

  await axios
    .post('/api/files/_upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        upload.value.progress = 100 * (progressEvent.loaded / progressEvent.total)
      }
    })
    .then(async (response) => {
      upload.value.status = STATUS.done
      upload.value.message = response.data.message
    })
    .catch((error) => {
      upload.value.status = STATUS.stopped
      upload.value.message = error.message
    })
  await fetchDatabases({ refresh: true })
}

const uploadFileHandle = async (event) => {
  const file = event.target?.files?.[0] || event.dataTransfer.files?.[0]
  if (!file) return
  const { name, type } = file
  if (!name || !type) return
  const isSupported = ['csv', 'xls', 'xlsx', 'json'].includes(type.split('/')[1])
  if (!isSupported) return
  await uploadFile(file)
}
</script>
