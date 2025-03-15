<template>
  <base-field :name="name">
    <div class="relative block w-full max-w-lg">
      <Field
        :name="props.name"
        :type="props.type"
        v-model="model"
        :placeholder="props.placeholder"
        class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
        :rules="props.rules"
      />
      <div class="input-slot-container">
        <slot />
      </div>
    </div>
    <ErrorMessage :name="props.name" class="sm:text-sm text-red-400" />
  </base-field>
</template>

<script setup lang="ts">
import BaseField from '../components/BaseField.vue'
// Name from props
import { defineProps, computed, defineEmits } from 'vue'
import { configure, Field, ErrorMessage, defineRule } from 'vee-validate'
import { localize } from '@vee-validate/i18n'
import { required } from '@vee-validate/rules'

configure({
  generateMessage: localize({
    en: {
      messages: {
        required: 'this field is required'
      }
    }
  })
})

defineRule('required', required)

interface Props {
  name: string
  modelValue: string | number
  placeholder?: string
  rules?: string
  type?: string
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '',
  type: 'text',
  rules: ''
})

const emit = defineEmits(['update:modelValue'])

const model = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})
</script>

<style scoped>
.input-slot-container {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  height: 100%;
  display: flex;
  align-items: center;
}
</style>
