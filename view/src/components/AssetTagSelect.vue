<script setup lang="ts">
import { Button } from '@/components/ui/button'
import {
  Combobox,
  ComboboxAnchor,
  ComboboxEmpty,
  ComboboxGroup,
  ComboboxInput,
  ComboboxItem,
  ComboboxList
} from '@/components/ui/combobox'
import {
  TagsInput,
  TagsInputInput,
  TagsInputItem,
  TagsInputItemDelete,
  TagsInputItemText
} from '@/components/ui/tags-input'
import { useCatalogStore, type AssetTag } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { ChevronsUpDown } from 'lucide-vue-next'
import { useFilter } from 'reka-ui'
import { computed, ref } from 'vue'
import ComboboxTrigger from './ui/combobox/ComboboxTrigger.vue'

interface Props {
  modelValue: AssetTag[]
  disabled?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: AssetTag[]): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const catalogStore = useCatalogStore()
const contextsStore = useContextsStore()

const open = ref(false)
const searchTerm = ref('')
const loading = ref(false)

const { contains } = useFilter({ sensitivity: 'base' })

// Filter available tags to only show ones not already selected
const filteredTags = computed(() => {
  const selectedIds = new Set(props.modelValue.map((tag) => tag.id))
  const options = catalogStore.tagsArray.filter((tag) => !selectedIds.has(tag.id))
  return searchTerm.value
    ? options.filter((option) => contains(option.name, searchTerm.value))
    : options
})

// Check if search term matches an existing tag name (case-insensitive)
const isNewTag = computed(() => {
  if (!searchTerm.value.trim()) return false
  const trimmedSearch = searchTerm.value.trim().toLowerCase()
  return !catalogStore.tagsArray.some((tag) => tag.name.toLowerCase() === trimmedSearch)
})

async function handleSelectTag(tagId: string) {
  const tag = catalogStore.tagsArray.find((t) => t.id === tagId)
  if (tag) {
    emit('update:modelValue', [...props.modelValue, tag])
    searchTerm.value = ''
  }

  if (filteredTags.value.length === 0) {
    open.value = false
  }
}

async function handleCreateTag() {
  if (!searchTerm.value.trim() || !contextsStore.contextSelected?.id) return
  if (!isNewTag.value) return

  try {
    loading.value = true
    const newTag = await catalogStore.createTag(contextsStore.contextSelected.id, {
      name: searchTerm.value.trim()
    })

    emit('update:modelValue', [...props.modelValue, newTag])
    searchTerm.value = ''
    open.value = false
  } catch (error) {
    console.error('Failed to create tag:', error)
  } finally {
    loading.value = false
  }
}

function handleRemoveTag(tagId: string) {
  emit(
    'update:modelValue',
    props.modelValue.filter((tag) => tag.id !== tagId)
  )
}

async function handleKeyDown(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()

    if (isNewTag.value && searchTerm.value.trim()) {
      await handleCreateTag()
    }
  }
}
</script>

<template>
  <Combobox v-model:open="open" :ignore-filter="true" :disabled="disabled">
    <ComboboxAnchor as-child>
      <TagsInput class="px-2 gap-2 w-full">
        <div class="flex items-center w-full">
          <div class="flex gap-2 flex-wrap items-center flex-1 min-w-0">
            <TagsInputItem
              v-for="tag in modelValue"
              :key="tag.id"
              :value="tag.name"
              :disabled="disabled"
            >
              <TagsInputItemText>{{ tag.name }}</TagsInputItemText>
              <TagsInputItemDelete @click="handleRemoveTag(tag.id)" />
            </TagsInputItem>

            <ComboboxInput v-model="searchTerm" as-child>
              <TagsInputInput
                placeholder="Search or create tag..."
                class="flex-1 min-w-[100px] px-0 py-1 border-none focus-visible:ring-0 h-auto"
                :disabled="disabled"
                @keydown.enter="handleKeyDown"
              />
            </ComboboxInput>
          </div>

          <ComboboxTrigger as-child>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              class="flex-shrink-0"
              :disabled="disabled"
            >
              <ChevronsUpDown :class="['h-4 w-4 transition-transform', open && 'rotate-180']" />
            </Button>
          </ComboboxTrigger>
        </div>
      </TagsInput>
    </ComboboxAnchor>

    <ComboboxList class="combobox-content-width-full">
      <ComboboxEmpty>
        <div class="py-2 px-2 text-sm text-muted-foreground">
          <span v-if="loading">Creating tag...</span>
          <span v-else-if="isNewTag && searchTerm.trim()">
            Press <kbd class="px-1 bg-muted rounded">Enter</kbd> to create "{{ searchTerm.trim() }}"
          </span>
          <span v-else>No tags found</span>
        </div>
      </ComboboxEmpty>
      <ComboboxGroup class="max-h-60 overflow-y-auto">
        <ComboboxItem
          v-for="tag in filteredTags"
          :key="tag.id"
          :value="tag.id"
          @select.prevent="
            (ev) => {
              if (typeof ev.detail.value === 'string') {
                handleSelectTag(ev.detail.value)
              }
            }
          "
        >
          <div class="flex flex-col gap-0.5 w-full">
            <span class="font-medium">{{ tag.name }}</span>
            <span
              v-if="tag.description"
              class="text-xs text-muted-foreground break-words whitespace-normal"
            >
              {{ tag.description }}
            </span>
          </div>
        </ComboboxItem>
      </ComboboxGroup>
    </ComboboxList>
  </Combobox>
</template>
