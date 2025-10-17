<template>
  <div class="flex items-center gap-2 p-3 bg-white border-b border-slate-200">
    <span class="text-sm font-medium text-muted-foreground">Quick filters:</span>
    <Button
      v-for="filter in quickFilters"
      :key="filter.status"
      :variant="selectedStatus === filter.status ? 'default' : 'outline'"
      size="sm"
      @click="$emit('select-status', filter.status)"
      class="gap-1.5"
    >
      <component :is="filter.icon" class="h-3.5 w-3.5" />
      {{ filter.label }}
      <Badge v-if="filter.count > 0" variant="secondary" class="ml-1 text-xs">
        {{ filter.count }}
      </Badge>
    </Button>
    <Button
      :variant="selectedStatus === '__all__' ? 'default' : 'ghost'"
      size="sm"
      @click="$emit('select-status', '__all__')"
    >
      All Assets
    </Button>
  </div>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { AssetStatus } from '@/types/catalog'
import { AlertCircle, Clock } from 'lucide-vue-next'
import { computed } from 'vue'

interface Props {
  selectedStatus: string
  assetsByStatus: Record<AssetStatus, any[]>
}

const props = defineProps<Props>()

defineEmits<{
  'select-status': [status: string]
}>()

const quickFilters = computed(() => [
  {
    status: 'requires_validation',
    label: 'Requires Validation',
    icon: AlertCircle,
    count: props.assetsByStatus.requires_validation?.length || 0,
    priority: 1
  },
  {
    status: 'needs_review',
    label: 'Needs Review',
    icon: Clock,
    count: props.assetsByStatus.needs_review?.length || 0,
    priority: 2
  }
])
</script>
