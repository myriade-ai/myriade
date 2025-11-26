<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <BookA />
        <span>{{ modelValue.name }}</span>
      </CardTitle>
      <CardAction>
        <Button
          v-if="isEditable"
          variant="link"
          class="text-green-600"
          @click="handleApprove"
          :disabled="isProcessing"
          :is-loading="isProcessing"
        >
          <template #loading>Executing...</template>
          Approve
        </Button>
      </CardAction>
    </CardHeader>
    <CardContent class="space-y-2">
      <div>
        <label class="font-semibold block mb-1">Definition</label>
        <Textarea class="bg-card" v-model="termDefinitionModel" :disabled="!isEditable" rows="4" />
      </div>

      <div>
        <label class="font-semibold block mb-1">Synonyms</label>
        <TagsInput
          v-model="termSynonymsModel"
          :disabled="!isEditable"
          :class="!isEditable ? 'opacity-50' : ''"
          v-if="termSynonymsModel.length > 0"
        >
          <TagsInputItem v-for="synonym in termSynonymsModel" :key="synonym" :value="synonym">
            <TagsInputItemText />
            <TagsInputItemDelete v-if="isEditable" />
          </TagsInputItem>
          <TagsInputInput v-if="isEditable" placeholder="Add synonym" />
        </TagsInput>
      </div>

      <div>
        <label class="font-semibold block mb-1">Business Domains</label>

        <TagsInput
          v-model="termBusinessDomainsModel"
          :disabled="!isEditable"
          :class="!isEditable ? 'opacity-50' : ''"
          v-if="termBusinessDomainsModel.length > 0"
        >
          <TagsInputItem v-for="domain in termBusinessDomainsModel" :key="domain" :value="domain">
            <TagsInputItemText />
            <TagsInputItemDelete v-if="isEditable" />
          </TagsInputItem>
          <TagsInputInput v-if="isEditable" placeholder="Add domain" />
        </TagsInput>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import Button from '@/components/ui/button/Button.vue'
import {
  TagsInput,
  TagsInputInput,
  TagsInputItem,
  TagsInputItemDelete,
  TagsInputItemText
} from '@/components/ui/tags-input'
import Textarea from '@/components/ui/textarea/Textarea.vue'
import { computed } from 'vue'
import type { CatalogTermState } from '@/types/catalog'
import { Card, CardAction, CardContent, CardHeader, CardTitle } from './ui/card'
import { BookA } from 'lucide-vue-next'

const props = defineProps<{
  modelValue: CatalogTermState
  isEditable: boolean
  isProcessing: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', payload: CatalogTermState): void
  (e: 'approve'): void
}>()

const modelValue = computed(() => props.modelValue)

const updateModelValue = (patch: Partial<CatalogTermState>) => {
  emit('update:modelValue', {
    ...modelValue.value,
    ...patch
  })
}

const termDefinitionModel = computed<string>({
  get: () => {
    const raw = modelValue.value?.definition
    return typeof raw === 'string' ? raw : ''
  },
  set: (val: string) => {
    updateModelValue({ definition: val })
  }
})

const termSynonymsModel = computed<string[]>({
  get: () => {
    const source = modelValue.value.synonyms
    if (!Array.isArray(source)) return []
    const result: string[] = []
    const seen = new Set<string>()
    source.forEach((entry) => {
      const normalized = typeof entry === 'string' ? entry.trim() : String(entry ?? '').trim()
      if (normalized && !seen.has(normalized)) {
        seen.add(normalized)
        result.push(normalized)
      }
    })
    return result
  },
  set: (val: string[]) => {
    const normalized: string[] = []
    const seen = new Set<string>()
    val.forEach((entry) => {
      const trimmed = entry.trim()
      if (trimmed && !seen.has(trimmed)) {
        seen.add(trimmed)
        normalized.push(trimmed)
      }
    })
    updateModelValue({ synonyms: normalized })
  }
})

const termBusinessDomainsModel = computed<string[]>({
  get: () => {
    const source = modelValue.value.business_domains
    if (!Array.isArray(source)) return []
    const result: string[] = []
    const seen = new Set<string>()
    source.forEach((entry) => {
      const normalized = typeof entry === 'string' ? entry.trim() : String(entry ?? '').trim()
      if (normalized && !seen.has(normalized)) {
        seen.add(normalized)
        result.push(normalized)
      }
    })
    return result
  },
  set: (val: string[]) => {
    const normalized: string[] = []
    const seen = new Set<string>()
    val.forEach((entry) => {
      const trimmed = entry.trim()
      if (trimmed && !seen.has(trimmed)) {
        seen.add(trimmed)
        normalized.push(trimmed)
      }
    })
    updateModelValue({ business_domains: normalized })
  }
})

const handleApprove = () => {
  emit('approve')
}

const isEditable = computed(() => props.isEditable)
const isProcessing = computed(() => props.isProcessing)
</script>
