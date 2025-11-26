<template>
  <Badge v-if="status === 'published_by_ai'" :class="badgeClass" variant="secondary">
    Published by AI
  </Badge>
  <Badge
    v-else-if="status === 'human_authored'"
    :class="cn('bg-green-500/10 text-green-700 dark:text-green-400', badgeClass)"
    variant="secondary"
  >
    Published by User
  </Badge>
  <Badge
    v-else-if="status === 'validated'"
    :class="cn('bg-green-500/10 text-green-700 dark:text-green-400', badgeClass)"
    variant="secondary"
  >
    Validated
  </Badge>
  <Badge
    v-else-if="status === 'needs_review' || status === 'requires_validation'"
    :class="cn('bg-yellow-500/10 text-yellow-700 dark:text-yellow-400', badgeClass)"
    variant="secondary"
  >
    Waiting for review
  </Badge>
  <Badge
    v-else
    :class="cn('bg-orange-500/10 text-orange-700 dark:text-orange-400', badgeClass)"
    variant="secondary"
  >
    Unverified
  </Badge>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { AssetStatus } from '@/stores/catalog'

interface Props {
  status?: AssetStatus | null
  badgeClass?: string
}

defineProps<Props>()
</script>
