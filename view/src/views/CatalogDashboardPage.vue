<template>
  <div class="h-full w-full flex flex-col bg-background">
    <PageHeader title="Overview" sticky>
      <template #actions>
        <Button variant="outline" size="sm" @click="refetch" :disabled="isFetching">
          <RotateCw class="h-4 w-4 mr-2" :class="{ 'animate-spin': isFetching }" />
          {{ isFetching ? 'Syncing...' : 'Sync' }}
        </Button>
        <Button variant="outline" size="sm" @click="startScan" :disabled="isFetching">
          <SparklesIcon class="h-4 w-4 mr-2" />
          Launch Smart Scan
        </Button>
      </template>
    </PageHeader>

    <!-- Content -->
    <div class="flex-1 overflow-auto">
      <div v-if="isLoading" class="flex items-center justify-center h-full">
        <div class="text-center">
          <div
            class="animate-spin rounded-full h-8 w-8 border-2 border-muted-foreground/30 border-t-muted-foreground mx-auto mb-4"
          />
          <p class="text-sm text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>

      <div v-else-if="error" class="border-b border-border px-6 py-4">
        <div class="bg-destructive/10 border border-destructive/20 rounded p-3">
          <h3 class="font-semibold text-destructive text-sm">Error loading dashboard</h3>
          <p class="text-xs text-destructive/80 mt-1">{{ error?.message }}</p>
          <Button variant="outline" size="sm" @click="refetch" class="mt-3 h-8">Retry</Button>
        </div>
      </div>

      <div v-else-if="data">
        <!-- Overall Stats Section -->
        <div class="border-b border-border">
          <div class="px-6 py-4">
            <div class="flex items-center justify-between mb-3">
              <h2 class="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                Overall Completion
              </h2>
              <div class="flex items-baseline gap-2">
                <span class="text-xs text-muted-foreground leading-none">
                  {{ data.overall.assets_validated.toLocaleString() }}
                  / {{ data.overall.total_assets.toLocaleString() }}
                </span>
                <span class="text-lg font-bold leading-none"
                  >{{ data.overall.completion_percentage }}%</span
                >
              </div>
            </div>
            <ProgressBar :percentage="data.overall.completion_percentage" size="md" class="mb-4" />
            <div class="grid grid-cols-3 gap-6">
              <button
                class="border-r border-border flex flex-col justify-center items-center gap-1 hover:bg-muted/50 rounded-lg py-2 transition-colors cursor-pointer"
                @click="navigateToAssets({ status: 'unverified' })"
              >
                <div class="text-2xl font-bold">
                  {{ data.overall.total_assets.toLocaleString() }}
                </div>
                <div class="text-xs text-muted-foreground flex items-center gap-1">
                  Assets to Catalog
                </div>
              </button>
              <button
                class="border-r border-border flex flex-col justify-center items-center gap-1 hover:bg-muted/50 rounded-lg py-2 transition-colors cursor-pointer"
                @click="navigateToAssets({ status: 'published' })"
              >
                <div class="text-2xl font-bold text-green-600 dark:text-green-400">
                  {{ data.overall.assets_validated.toLocaleString() }}
                </div>
                <div class="text-xs text-muted-foreground">Validated</div>
              </button>
              <button
                class="flex flex-col justify-center items-center gap-1 hover:bg-muted/50 rounded-lg py-2 transition-colors cursor-pointer"
                @click="navigateToAssets({ ai: 'true' })"
              >
                <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">
                  {{ data.overall.assets_with_ai_suggestions.toLocaleString() }}
                </div>
                <div class="text-xs text-muted-foreground">To Review</div>
              </button>
            </div>
          </div>
        </div>

        <!-- Databases Section Header -->
        <div class="px-6 py-4">
          <h2 class="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Databases
          </h2>
        </div>

        <!-- Databases List (Edge-to-edge) -->
        <div class="border-t border-border divide-y divide-border">
          <DatabaseCard v-for="db in data.databases" :key="db.database_id" :database="db" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import PageHeader from '@/components/PageHeader.vue'
import DatabaseCard from '@/components/catalog/DatabaseCard.vue'
import ProgressBar from '@/components/catalog/ProgressBar.vue'
import { useCatalogAssetsQuery } from '@/components/catalog/useCatalogQuery'
import { Button } from '@/components/ui/button'
import { computeDashboardStats } from '@/composables/useDashboardStats'
import { RotateCw, SparklesIcon } from 'lucide-vue-next'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const assetsQuery = useCatalogAssetsQuery()
const { data: catalogAssets, isLoading, error, isFetching, refetch } = assetsQuery
const router = useRouter()

const data = computeDashboardStats(computed(() => catalogAssets.value))

const startScan = () => {
  router.push({ name: 'SmartScanPage' })
}

const navigateToAssets = (filters?: { status?: string; ai?: string }) => {
  router.push({
    name: 'AssetPage',
    state: filters
  })
}
</script>
