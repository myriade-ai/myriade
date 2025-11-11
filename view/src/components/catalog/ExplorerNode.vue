<template>
  <div>
    <div
      class="group relative"
      @mouseenter="showActions = true"
      @mouseleave="showActions = false"
    >
      <button
        type="button"
        class="flex w-full flex-col items-start gap-1 rounded-lg px-2 py-1.5 text-left text-sm font-medium transition-all duration-200"
        :class="[
          isSelected
            ? 'bg-gradient-to-r from-blue-50 to-slate-100 text-primary-900 ring-1 ring-primary-400 shadow-sm'
            : 'text-foreground hover:bg-gradient-to-r hover:from-slate-100 hover:to-stone-100'
        ]"
        @click.stop="handleSelect"
      >
        <div class="flex w-full items-center gap-2">
          <ChevronRight
            class="h-4 w-4 flex-shrink-0 text-muted-foreground cursor-pointer"
            :class="expanded ? 'rotate-90' : ''"
            @click.stop="emit('toggle')"
          />
          <component :is="iconComponent" class="h-4 w-4 flex-shrink-0 text-primary-600" />
          <span class="break-words flex-1 truncate">{{ label }}</span>
          <!-- Action buttons -->
          <div
            v-if="showActions"
            class="flex items-center gap-0.5 flex-shrink-0 ml-1"
            @click.stop
          >
            <Button
              v-if="canAddToAnalysis"
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
              v-if="canReviewWithAI"
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
      </button>
    </div>
    <div v-if="expanded">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ChevronRight,
  Database,
  FolderTree,
  Table as TableIcon,
  View as ViewIcon,
  PlusIcon,
  CheckIcon,
  SparklesIcon
} from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { Button } from '@/components/ui/button'
import { useCatalogStore } from '@/stores/catalog'
import { useConversationsStore } from '@/stores/conversations'
import { useContextsStore } from '@/stores/contexts'
import { useRouter } from 'vue-router'

const props = defineProps<{
  label: string
  icon: 'database' | 'schema' | 'table' | 'view'
  expanded: boolean
  isSelected?: boolean
  assetId?: string
}>()

const emit = defineEmits<{
  (e: 'toggle'): void
  (e: 'select'): void
}>()

const catalogStore = useCatalogStore()
const conversationsStore = useConversationsStore()
const contextsStore = useContextsStore()
const router = useRouter()
const showActions = ref(false)

const iconComponent = computed(() => {
  if (props.icon === 'database') return Database
  if (props.icon === 'table') return TableIcon
  if (props.icon === 'view') return ViewIcon
  return FolderTree
})

// Only show add to analysis for tables/views (not for databases/schemas)
const canAddToAnalysis = computed(() => {
  return props.assetId && (props.icon === 'table' || props.icon === 'view')
})

// Only show review with AI for tables/views (not for databases/schemas)
const canReviewWithAI = computed(() => {
  return props.assetId && (props.icon === 'table' || props.icon === 'view')
})

const isAssetSelected = computed(() => {
  return props.assetId ? catalogStore.isAssetSelected(props.assetId) : false
})

function handleSelect() {
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
    
    let message = ''
    if (props.icon === 'view') {
      message = `Please review the view "${props.label}" (id: ${props.assetId}) and suggest improvements to its description, tags`
    } else {
      message = `Please review the table "${props.label}" (id: ${props.assetId}) and suggest improvements to its description, tags`
    }

    await conversationsStore.sendMessage(conversation.id, message, 'text')
    router.push({ name: 'ChatPage', params: { id: conversation.id.toString() } })
  } catch (error) {
    console.error('Error creating conversation:', error)
  }
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
