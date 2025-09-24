<template>
  <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 my-3">
    <div class="flex items-start gap-3">
      <component :is="statusIcon" class="w-5 h-5 mt-0.5 flex-shrink-0" :class="statusIconClass" />

      <div class="flex-1 text-sm">
        <h4 class="text-sm font-medium text-yellow-800 mb-2">
          {{ proposal.title || 'Catalog Operation Confirmation Required' }}
        </h4>

        <p v-if="showAutoAppliedMessage" class="text-yellow-700 mb-3">
          These changes were applied automatically by AI. Approve to mark them as human-reviewed.
        </p>

        <p v-else-if="showPendingMessage" class="text-yellow-700 mb-3">
          This operation will update your data catalog. Review the proposed changes before
          approving.
        </p>

        <p v-else-if="isApproved" class="text-green-700 mb-3">
          Operation approved and marked as reviewed.
        </p>

        <p v-else-if="isRejected" class="text-red-700 mb-3">
          Operation rejected. No catalog changes were made.
        </p>

        <div v-if="assetMetadata" class="mb-4 space-y-1 text-yellow-700">
          <div>
            <span class="font-semibold text-yellow-800">Asset:</span> {{ assetMetadata.name }}
          </div>
          <div v-if="assetMetadata.type">
            <span class="font-semibold text-yellow-800">Type:</span> {{ assetMetadata.type }}
          </div>
        </div>

        <div v-else-if="termMetadata" class="mb-4 space-y-1 text-yellow-700">
          <div>
            <span class="font-semibold text-yellow-800">Term:</span> {{ termMetadata.name }}
          </div>
        </div>

        <div v-if="entityType === 'asset'" class="space-y-4">
          <div>
            <label class="font-semibold text-yellow-800 block mb-1">Description</label>
            <p class="text-xs text-gray-500 mb-2">
              Current: <span class="text-gray-700">{{ currentDescriptionDisplay }}</span>
            </p>
            <Textarea
              class="bg-white"
              v-model="assetDescriptionModel"
              :disabled="!isEditable"
              rows="4"
            />
          </div>

          <div>
            <label class="font-semibold text-yellow-800 block mb-1">Tags</label>
            <p class="text-xs text-gray-500 mb-2">
              Current: <span class="text-gray-700">{{ currentTagsDisplay }}</span>
            </p>
            <TagsInput
              v-model="assetTagsModel"
              :disabled="!isEditable"
              :class="!isEditable ? 'opacity-50' : ''"
            >
              <TagsInputItem v-for="tag in assetTagsModel" :key="tag" :value="tag">
                <TagsInputItemText />
                <TagsInputItemDelete v-if="isEditable" />
              </TagsInputItem>
              <TagsInputInput v-if="isEditable" placeholder="Add tag" />
            </TagsInput>
          </div>
        </div>

        <div v-else-if="entityType === 'term'" class="space-y-4">
          <div>
            <label class="font-semibold text-yellow-800 block mb-1">Definition</label>
            <p class="text-xs text-gray-500 mb-2">
              Current: <span class="text-gray-700">{{ currentDefinitionDisplay }}</span>
            </p>
            <Textarea
              class="bg-white"
              v-model="termDefinitionModel"
              :disabled="!isEditable"
              rows="4"
            />
          </div>

          <div>
            <label class="font-semibold text-yellow-800 block mb-1">Synonyms</label>
            <p class="text-xs text-gray-500 mb-2">
              Current: <span class="text-gray-700">{{ currentSynonymsDisplay }}</span>
            </p>
            <TagsInput
              v-model="termSynonymsModel"
              :disabled="!isEditable"
              :class="!isEditable ? 'opacity-50' : ''"
            >
              <TagsInputItem v-for="synonym in termSynonymsModel" :key="synonym" :value="synonym">
                <TagsInputItemText />
                <TagsInputItemDelete v-if="isEditable" />
              </TagsInputItem>
              <TagsInputInput v-if="isEditable" placeholder="Add synonym" />
            </TagsInput>
          </div>

          <div>
            <label class="font-semibold text-yellow-800 block mb-1">Business Domains</label>
            <p class="text-xs text-gray-500 mb-2">
              Current: <span class="text-gray-700">{{ currentBusinessDomainsDisplay }}</span>
            </p>
            <TagsInput
              v-model="termBusinessDomainsModel"
              :disabled="!isEditable"
              :class="!isEditable ? 'opacity-50' : ''"
            >
              <TagsInputItem
                v-for="domain in termBusinessDomainsModel"
                :key="domain"
                :value="domain"
              >
                <TagsInputItemText />
                <TagsInputItemDelete v-if="isEditable" />
              </TagsInputItem>
              <TagsInputInput v-if="isEditable" placeholder="Add domain" />
            </TagsInput>
          </div>
        </div>

        <div class="flex gap-2 mt-3" v-if="isEditable">
          <Button
            variant="default"
            @click="handleApprove"
            :disabled="isProcessing"
            :is-loading="isProcessing"
          >
            <template #loading>Executing...</template>
            Approve
          </Button>
        </div>
      </div>
    </div>
  </div>
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
import { socket } from '@/plugins/socket'
import { CheckCircleIcon, ExclamationTriangleIcon, XCircleIcon } from '@heroicons/vue/24/outline'
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps<{
  proposal: Record<string, any>
  functionCallId: string | undefined
}>()

const route = useRoute()
const conversationId = computed(() =>
  route.params.id === 'new' ? null : (route.params.id as string)
)

const isProcessing = ref(false)

const status = computed(() => props.proposal?.status ?? 'pending_review')
const isRejected = computed(() => status.value === 'rejected')
const showAutoAppliedMessage = computed(() => status.value === 'pending_review')
const showPendingMessage = computed(() => status.value === 'pending')
const isEditable = computed(() => showAutoAppliedMessage.value || showPendingMessage.value)
const isApproved = computed(() => !isEditable.value && !isRejected.value)

const statusIcon = computed(() => {
  if (isApproved.value) return CheckCircleIcon
  if (isRejected.value) return XCircleIcon
  return ExclamationTriangleIcon
})

const statusIconClass = computed(() => {
  if (isApproved.value) return 'text-green-500'
  if (isRejected.value) return 'text-red-500'
  return 'text-yellow-400'
})

const entity = computed<Record<string, any>>(() => {
  const raw = props.proposal?.entity
  return raw && typeof raw === 'object' ? (raw as Record<string, any>) : {}
})

const entityType = computed(() => (entity.value?.type as string | undefined) ?? '')

const currentState = computed<Record<string, unknown>>(() => {
  const current = props.proposal?.current
  if (current && typeof current === 'object') {
    return current as Record<string, unknown>
  }
  return {}
})

const localProposed = ref<Record<string, unknown>>({})

const ensureStringArray = (value: unknown): string[] => {
  if (!Array.isArray(value)) return []
  return value
    .map((item) => (typeof item === 'string' ? item.trim() : String(item ?? '')))
    .filter((item) => item.length > 0)
}

const normalizeStringArray = (value: string[]): string[] => {
  const seen = new Set<string>()
  const result: string[] = []
  value.forEach((item) => {
    const trimmed = item.trim()
    if (trimmed.length > 0 && !seen.has(trimmed)) {
      seen.add(trimmed)
      result.push(trimmed)
    }
  })
  return result
}

const initializeLocalProposed = () => {
  const proposedRaw = props.proposal?.proposed
  let base: Record<string, unknown>
  if (proposedRaw && typeof proposedRaw === 'object') {
    base = proposedRaw
  } else {
    base = {}
  }

  if (entityType.value === 'asset') {
    if (typeof base.description !== 'string') {
      base.description =
        typeof currentState.value.description === 'string'
          ? (currentState.value.description as string)
          : ''
    }
    base.tags = ensureStringArray(base.tags ?? currentState.value.tags)
  } else if (entityType.value === 'term') {
    if (typeof base.definition !== 'string') {
      base.definition =
        typeof currentState.value.definition === 'string'
          ? (currentState.value.definition as string)
          : ''
    }
    base.synonyms = ensureStringArray(base.synonyms ?? currentState.value.synonyms)
    base.business_domains = ensureStringArray(
      base.business_domains ?? currentState.value.business_domains
    )
    if (typeof base.name !== 'string' && typeof entity.value?.name === 'string') {
      base.name = entity.value.name
    }
  }

  localProposed.value = base
}

watch(
  () => props.proposal,
  () => {
    initializeLocalProposed()
  },
  { immediate: true }
)

const assetDescriptionModel = computed({
  get: () =>
    typeof localProposed.value.description === 'string'
      ? (localProposed.value.description as string)
      : '',
  set: (val: string) => {
    localProposed.value = {
      ...localProposed.value,
      description: val
    }
  }
})

const assetTagsModel = computed<string[]>({
  get: () => ensureStringArray(localProposed.value.tags),
  set: (val: string[]) => {
    localProposed.value = {
      ...localProposed.value,
      tags: normalizeStringArray(val)
    }
  }
})

const termDefinitionModel = computed({
  get: () =>
    typeof localProposed.value.definition === 'string'
      ? (localProposed.value.definition as string)
      : '',
  set: (val: string) => {
    localProposed.value = {
      ...localProposed.value,
      definition: val
    }
  }
})

const termSynonymsModel = computed<string[]>({
  get: () => ensureStringArray(localProposed.value.synonyms),
  set: (val: string[]) => {
    localProposed.value = {
      ...localProposed.value,
      synonyms: normalizeStringArray(val)
    }
  }
})

const termBusinessDomainsModel = computed<string[]>({
  get: () => ensureStringArray(localProposed.value.business_domains),
  set: (val: string[]) => {
    localProposed.value = {
      ...localProposed.value,
      business_domains: normalizeStringArray(val)
    }
  }
})

const emptyValueDisplay = ' X'

const formatDisplay = (value: unknown): string => {
  if (value === null || value === undefined) return emptyValueDisplay
  if (Array.isArray(value)) {
    if (value.length === 0) return emptyValueDisplay
    return value.map((item) => String(item)).join(', ')
  }
  if (typeof value === 'string') {
    return value.trim().length > 0 ? value : emptyValueDisplay
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

const currentDescriptionDisplay = computed(() => formatDisplay(currentState.value?.description))

const currentTagsDisplay = computed(
  () => ensureStringArray(currentState.value?.tags).join(', ') || emptyValueDisplay
)

const currentDefinitionDisplay = computed(() => formatDisplay(currentState.value?.definition))

const currentSynonymsDisplay = computed(
  () => ensureStringArray(currentState.value?.synonyms).join(', ') || emptyValueDisplay
)

const currentBusinessDomainsDisplay = computed(
  () => ensureStringArray(currentState.value?.business_domains).join(', ') || emptyValueDisplay
)

const buildProposedPayload = () => {
  const payload = localProposed.value ?? ({} as Record<string, unknown>)

  if (entityType.value === 'asset') {
    payload.description = assetDescriptionModel.value.trim()
    payload.tags = normalizeStringArray(assetTagsModel.value)
  } else if (entityType.value === 'term') {
    payload.definition = termDefinitionModel.value.trim()
    payload.synonyms = normalizeStringArray(termSynonymsModel.value)
    payload.business_domains = normalizeStringArray(termBusinessDomainsModel.value)
    if (typeof payload.name !== 'string' && typeof entity.value?.name === 'string') {
      payload.name = entity.value.name
    }
  }

  localProposed.value = {
    ...localProposed.value,
    ...payload
  }

  return payload
}

const assetMetadata = computed(() => {
  if (entityType.value !== 'asset') return null
  return {
    name:
      (typeof entity.value?.name === 'string' && entity.value.name) ||
      (typeof localProposed.value.name === 'string' ? (localProposed.value.name as string) : ''),
    urn: entity.value?.urn as string | undefined,
    type: entity.value?.type as string | undefined
  }
})

const termMetadata = computed(() => {
  if (entityType.value !== 'term') return null
  const proposedName =
    typeof localProposed.value.name === 'string'
      ? (localProposed.value.name as string)
      : typeof entity.value?.name === 'string'
        ? entity.value.name
        : ''
  return {
    name: proposedName
  }
})

const handleApprove = async () => {
  if (!conversationId.value || !props.functionCallId) return
  try {
    isProcessing.value = true
    const proposedPayload = isEditable.value ? buildProposedPayload() : undefined
    socket.emit(
      'confirmCatalogOperation',
      conversationId.value,
      props.functionCallId,
      proposedPayload
    )
  } catch (error) {
    console.error('Failed to approve catalog entry:', error)
  } finally {
    isProcessing.value = false
  }
}
</script>
