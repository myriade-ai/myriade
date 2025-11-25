<template>
  <Badge
    v-if="status === 'published'"
    :class="cn('bg-green-500/10 text-green-700 dark:text-green-400', badgeClass)"
    variant="secondary"
    :title="publishedTooltip"
  >
    Published
  </Badge>
  <Badge
    v-else-if="status === 'draft'"
    :class="cn('bg-yellow-500/10 text-yellow-700 dark:text-yellow-400', badgeClass)"
    variant="secondary"
  >
    Draft
  </Badge>
  <Badge
    v-else
    :class="cn('bg-gray-500/10 text-gray-700 dark:text-gray-400', badgeClass)"
    variant="secondary"
  >
    Unverified
  </Badge>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { AssetStatus } from '@/stores/catalog'
import { computed } from 'vue'

interface Props {
  status?: AssetStatus | null
  badgeClass?: string
  publishedBy?: string | null
  publishedAt?: string | null
}

const props = defineProps<Props>()

const publishedTooltip = computed(() => {
  if (props.status !== 'published') return undefined

  const parts: string[] = []
  if (props.publishedBy) {
    const publishedByLabel = props.publishedBy === 'myriade-agent' ? 'AI Agent' : props.publishedBy
    parts.push(`by ${publishedByLabel}`)
  }
  if (props.publishedAt) {
    const date = new Date(props.publishedAt)
    parts.push(`on ${date.toLocaleDateString()}`)
  }

  return parts.length > 0 ? `Published ${parts.join(' ')}` : 'Published'
})
</script>
