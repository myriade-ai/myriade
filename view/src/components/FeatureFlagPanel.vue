<template>
  <div v-if="isDevelopment" class="fixed bottom-4 right-4 z-50">
    <Card v-if="isExpanded" class="mb-2 w-72 gap-0">
      <CardHeader class="pb-3">
        <div class="flex items-center justify-between">
          <CardTitle class="text-sm">Feature Flags</CardTitle>
          <span class="text-xs bg-muted px-2 py-1 rounded">DEV</span>
        </div>
      </CardHeader>
      <CardContent class="space-y-4">
        <div
          v-for="flag in featureFlags"
          :key="flag.code"
          class="flex items-center justify-between"
        >
          <div class="flex-1">
            <label :for="flag.code" class="text-sm font-medium cursor-pointer">
              {{ flag.name }}
            </label>
            <div class="text-xs text-muted-foreground">{{ flag.code }}</div>
          </div>
          <Switch
            :id="flag.code"
            :model-value="flag.enabled"
            @update:model-value="toggleFeatureFlag(flag.code)"
          />
        </div>
      </CardContent>
    </Card>

    <Button @click="isExpanded = !isExpanded" size="icon" class="h-12 w-12 rounded-full">
      {{ isExpanded ? '×' : '+' }}
    </Button>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { useFeatureFlagsStore } from '@/stores/featureFlags'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'

const featureFlagsStore = useFeatureFlagsStore()
const { featureFlags, isDevelopment, toggleFeatureFlag } = featureFlagsStore

const isExpanded = ref(false)
</script>
