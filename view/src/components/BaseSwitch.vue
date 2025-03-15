<template>
  <div class="flex items-center">
    <span class="text-sm mr-3">
      <span class="font-medium text-gray-900">
        <slot />
      </span>
    </span>
    <Switch
      v-model="switchValue"
      :class="[
        switchValue ? 'bg-blue-600' : 'bg-gray-200',
        'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2'
      ]"
    >
      <span
        aria-hidden="true"
        :class="[
          switchValue ? 'translate-x-5' : 'translate-x-0',
          'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out'
        ]"
      />
    </Switch>
  </div>
</template>

<script setup lang="ts">
import { ref, watchEffect, watch } from 'vue'
import { defineProps, defineEmits } from 'vue'
import { Switch } from '@headlessui/vue'

const props = defineProps({
  modelValue: {
    type: Boolean
  }
})

const emit = defineEmits(['update:modelValue'])

const switchValue = ref(props.modelValue)

watch(switchValue, (newValue) => {
  emit('update:modelValue', newValue)
})
</script>
