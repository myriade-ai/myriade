<template>
  <div class="mt-1 rounded-md p-4" :class="colorClass('bg', 50)">
    <div class="flex">
      <div class="flex-shrink-0">
        <iconComponent class="h-5 w-5" :class="colorClass('text', 400)" aria-hidden="true" />
      </div>
      <div class="flex-grow ml-3">
        <p class="text-sm font-medium" :class="colorClass('text', 800)">
          {{ title }}
        </p>
        <div class="mt-2 text-sm" :class="colorClass('text', 700)">
          <div
            v-if="progress >= 0"
            class="mx-auto block h-2 relative max-w-xl rounded-full overflow-hidden"
          >
            <div class="w-full h-full absolute" :class="colorClass('bg', 200)"></div>
            <div
              id="bar"
              class="h-full relative w-0"
              :style="{ width: progress + '%' }"
              :class="colorClass('bg', 500)"
            ></div>
          </div>
        </div>
        <div v-if="message" class="mt-2 text-sm" :class="colorClass('text', 700)">
          <p class="mt-2">{{ message }}</p>
        </div>
      </div>
      <div class="ml-auto pl-3" v-if="displayClose">
        <div class="-mx-1.5 -my-1.5">
          <button
            @click="handleClose"
            type="button"
            class="inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2"
            :class="[
              colorClass('bg', 50),
              colorClass('text', 500),
              colorClass('hover:bg', 100),
              colorClass('focus:ring-offset', 50),
              colorClass('focus:ring', 600)
            ]"
          >
            <span class="sr-only">Dismiss</span>
            <XMarkIcon class="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { CloudArrowUpIcon, CheckCircleIcon, XMarkIcon, XCircleIcon } from '@heroicons/vue/24/solid'
import { computed } from 'vue'

const props = defineProps({
  color: {
    type: String,
    default: 'blue'
  },
  title: {
    type: String,
    default: 'Uploading file... (15%)'
  },
  message: {
    type: String
  },
  progress: {
    type: Number,
    default: -1
  },
  displayClose: {
    type: Boolean,
    default: false
  }
})

const colorClass = (type: string, intensity: number | string) => {
  // Only for tailwind...
  return `${type}-${props.color}-${intensity}`
}

const iconComponent = computed(() => {
  if (props.color == 'green') return CheckCircleIcon
  else if (props.color == 'red') return XCircleIcon
  else return CloudArrowUpIcon
})

const emits = defineEmits(['close'])

const handleClose = () => {
  console.log('handleClose')
  emits('close')
}
</script>
