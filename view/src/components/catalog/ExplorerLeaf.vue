<template>
  <div
    class="group relative"
    @mouseenter="showActions = true"
    @mouseleave="showActions = false"
  >
    <button
      type="button"
      class="flex w-full flex-col gap-1 rounded-lg px-2 py-2 text-left text-sm transition-all duration-200"
      :class="[
        isSelected
          ? 'bg-gradient-to-r from-blue-50 to-slate-100 text-primary-900 ring-1 ring-primary-400 shadow-sm'
          : 'text-muted-foreground hover:bg-gradient-to-r hover:from-slate-100 hover:to-stone-100'
      ]"
      @click="handleClick"
    >
      <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-2 truncate flex-1">
          <component :is="iconComponent" class="h-4 w-4 flex-shrink-0 text-primary-600" />
          <span class="truncate text-foreground">{{ label }}</span>
        </div>
        <div class="flex items-center gap-1 flex-shrink-0">
          <span v-if="meta" class="text-xs text-muted-foreground">{{ meta }}</span>
          <!-- Action buttons -->
          <div
            v-if="showActions && assetId"
            class="flex items-center gap-0.5 ml-1"
            @click.stop
          >
            <Button
              variant="ghost"
              size="icon"
              class="h-6 w-6 hover:bg-primary-100"
              :title="isAssetSelected ? 'Remove from analysis' : 'Add to analysis'"
              @click.stop="handleAddToAnalysis"
            >
              <PlusIcon v-if="!isAssetSelected" class="h-3.5 w-3.5" />
              <CheckIcon v-else class="h-3.5 w-3.5 text-primary-600" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              class="h-6 w-6 hover:bg-purple-100"
              title="Review with AI"
              @click.stop="handleReviewWithAI"
            >
              <SparklesIcon class="h-3.5 w-3.5 text-purple-600" />
            </Button>
          </div>
        </div>
      </div>
    </button>
  </div>
</template>

<script setup lang="ts">
import { Columns3, PlusIcon, CheckIcon, SparklesIcon } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { Button } from '@/components/ui/button'
import { useCatalogStore } from '@/stores/catalog'
import { useConversationsStore } from '@/stores/conversations'
import { useContextsStore } from '@/stores/contexts'
import { useRouter } from 'vue-router'

const props = defineProps<{
  label: string
  isSelected?: boolean
  meta?: string
  assetId?: string
}>()

const emit = defineEmits<{
  (e: 'select'): void
}>()

const catalogStore = useCatalogStore()
const conversationsStore = useConversationsStore()
const contextsStore = useContextsStore()
const router = useRouter()
const showActions = ref(false)

const iconComponent = computed(() => Columns3)

const isAssetSelected = computed(() => {
  return props.assetId ? catalogStore.isAssetSelected(props.assetId) : false
})

function handleClick() {
  emit('select')
}

function handleAddToAnalysis() {
  if (!props.assetId) return
  
  // Enable selection mode if not already enabled
  if (!catalogStore.selectionMode) {
    catalogStore.selectionMode = true
  }
  
  catalogStore.toggleAssetSelection(props.assetId)
}

async function handleReviewWithAI() {
  if (!props.assetId) return
  
  const contextId = contextsStore.contextSelected?.id
  if (!contextId) return

  try {
    const conversation = await conversationsStore.createConversation(contextId)
    const message = `Please review the column "${props.label}" (id: ${props.assetId}) and suggest improvements to its description, tags`

    await conversationsStore.sendMessage(conversation.id, message, 'text')
    router.push({ name: 'ChatPage', params: { id: conversation.id.toString() } })
  } catch (error) {
    console.error('Error creating conversation:', error)
  }
}
</script>
