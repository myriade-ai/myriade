<template>
  <div
    class="px-6 py-4 border-b border-slate-200 bg-white/80 backdrop-blur-sm flex justify-between"
  >
    <div>
      <div class="flex flex-col gap-2">
        <div>
          <div class="flex items-center gap-2">
            <component :is="assetIcon" class="h-5 w-5 text-primary-600" />
            <h2 class="text-lg font-semibold leading-tight">
              {{ asset.name || assetLabel }}
            </h2>
          </div>
          <p class="text-sm text-muted-foreground">
            {{ tableSummary }}
          </p>
          <div
            v-if="asset?.type === 'TABLE'"
            class="mt-2 flex items-center gap-4 text-sm text-muted-foreground"
          >
            <span>{{ columnsCount }} columns</span>
          </div>
        </div>
      </div>
      <div v-if="asset.tags?.length" class="mt-3 flex flex-wrap gap-2">
        <Badge v-for="tag in asset.tags" :key="tag.id" variant="secondary" class="text-xs">
          {{ tag.name }}
        </Badge>
      </div>
    </div>
    <div class="flex items-start gap-2">
      <AssetBadgeStatus :status="asset.status" badge-class="text-sm" />
      <Button
        v-if="catalogStore.selectionMode"
        :variant="isSelected ? 'default' : 'ghost'"
        size="sm"
        class="-mt-1"
        @click="addToAnalysis"
      >
        <PlusIcon class="h-4 w-4" />
        {{ isSelected ? 'Added to Analysis' : 'Add to Analysis' }}
      </Button>
      <Button
        v-else-if="showReviewButton"
        variant="ghost"
        size="sm"
        class="-mt-1"
        @click="reviewWithAI"
      >
        <SparklesIcon class="h-4 w-4" />
        Review with AI
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import AssetBadgeStatus from '@/components/AssetBadgeStatus.vue'
import type { CatalogAsset } from '@/stores/catalog'
import { useCatalogStore } from '@/stores/catalog'
import { useConversationsStore } from '@/stores/conversations'
import { useContextsStore } from '@/stores/contexts'
import { computed, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { SparklesIcon, PlusIcon } from 'lucide-vue-next'

const catalogStore = useCatalogStore()

interface Props {
  asset: CatalogAsset
  assetIcon: Component
  assetLabel: string
  tableSummary: string
  columnsCount: number
}

const props = defineProps<Props>()

const conversationsStore = useConversationsStore()
const contextsStore = useContextsStore()
const router = useRouter()

const showReviewButton = computed(() => {
  const status = props.asset.status
  return !status || status === 'human_authored' || status === 'validated'
})

const isSelected = computed(() => {
  return catalogStore.isAssetSelected(props.asset.id)
})

function addToAnalysis() {
  // Toggle selection for this asset
  const includeChildren = props.asset.type === 'TABLE'
  catalogStore.toggleAssetSelection(props.asset.id, includeChildren)
}

async function reviewWithAI() {
  const contextId = contextsStore.contextSelected?.id
  if (!contextId) return

  const conversation = await conversationsStore.createConversation(contextId)

  let message = ''
  if (props.asset.type === 'TABLE') {
    message = `Please review the table "${props.asset.name}" (id: ${props.asset.id}) and suggest improvements to its description, tags`
  } else if (props.asset.type === 'COLUMN') {
    message = `Please review the column "${props.asset.name}" (id: ${props.asset.id}) and suggest improvements to its description, tags`
  }

  await conversationsStore.sendMessage(conversation.id, message, 'text')

  router.push({ name: 'ChatPage', params: { id: conversation.id.toString() } })
}
</script>
