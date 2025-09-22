<template>
  <div class="space-y-6">
    <!-- Statistics Overview -->
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <Card>
        <CardContent class="p-4">
          <div class="text-2xl font-bold">{{ stats.totalAssets }}</div>
          <div class="text-sm text-muted-foreground">Total Assets</div>
        </CardContent>
      </Card>
      <Card>
        <CardContent class="p-4">
          <div class="text-2xl font-bold">{{ stats.totalSources }}</div>
          <div class="text-sm text-muted-foreground">Data Sources</div>
        </CardContent>
      </Card>
      <Card>
        <CardContent class="p-4">
          <div class="text-2xl font-bold">{{ stats.totalTables }}</div>
          <div class="text-sm text-muted-foreground">Tables</div>
        </CardContent>
      </Card>
      <Card>
        <CardContent class="p-4">
          <div class="text-2xl font-bold">{{ stats.totalFields }}</div>
          <div class="text-sm text-muted-foreground">Fields</div>
        </CardContent>
      </Card>
      <Card>
        <CardContent class="p-4">
          <div class="text-2xl font-bold" :class="getQualityScoreColor(stats.avgQualityScore)">
            {{ stats.avgQualityScore }}%
          </div>
          <div class="text-sm text-muted-foreground">Avg Quality</div>
        </CardContent>
      </Card>
      <Card>
        <CardContent class="p-4">
          <div class="text-2xl font-bold">{{ stats.totalDailyUsage.toLocaleString() }}</div>
          <div class="text-sm text-muted-foreground">Daily Queries</div>
        </CardContent>
      </Card>
    </div>

    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold">Data Assets</h2>
        <p class="text-muted-foreground">Discover, explore, and understand your data assets</p>
      </div>
      <div class="flex items-center space-x-2">
        <Button
          :variant="viewType === 'grid' ? 'default' : 'outline'"
          size="sm"
          @click="viewType = 'grid'"
        >
          Grid
        </Button>
        <Button
          :variant="viewType === 'table' ? 'default' : 'outline'"
          size="sm"
          @click="viewType = 'table'"
        >
          Table
        </Button>
      </div>
    </div>

    <!-- Quick Access -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle class="text-lg">Most Popular Assets</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="space-y-3">
            <div
              v-for="asset in popularAssets"
              :key="asset.id"
              class="flex items-center justify-between p-2 rounded hover:bg-muted cursor-pointer"
              @click="handleAssetNavigation(asset)"
            >
              <div class="flex items-center space-x-2">
                <component :is="getAssetIcon(asset.assetType)" class="h-4 w-4" />
                <div>
                  <div class="font-medium text-sm">{{ asset.name }}</div>
                  <div class="text-xs text-muted-foreground">{{ asset.domain }}</div>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <Star class="h-3 w-3 text-yellow-500" />
                <span class="text-sm">{{ asset.popularityScore }}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle class="text-lg">Recently Updated</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="space-y-3">
            <div
              v-for="asset in recentAssets"
              :key="asset.id"
              class="flex items-center justify-between p-2 rounded hover:bg-muted cursor-pointer"
              @click="handleAssetNavigation(asset)"
            >
              <div class="flex items-center space-x-2">
                <component :is="getAssetIcon(asset.assetType)" class="h-4 w-4" />
                <div>
                  <div class="font-medium text-sm">{{ asset.name }}</div>
                  <div class="text-xs text-muted-foreground">{{ asset.domain }}</div>
                </div>
              </div>
              <div class="text-xs text-muted-foreground">
                {{ asset.lastUpdated }}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Search and Filters -->
    <div class="flex flex-col lg:flex-row gap-4">
      <div class="flex-1">
        <div class="relative">
          <Search
            class="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4"
          />
          <Input placeholder="Search data assets..." v-model="filters.searchTerm" class="pl-10" />
        </div>
      </div>

      <div class="flex flex-wrap gap-2 lg:gap-4">
        <Select v-model="selectedAssetType">
          <SelectTrigger class="w-[140px]">
            <SelectValue placeholder="Asset Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="type in availableAssetTypes" :key="type" :value="type">
              {{ type }}
            </SelectItem>
          </SelectContent>
        </Select>

        <Select v-model="selectedDomain">
          <SelectTrigger class="w-[160px]">
            <SelectValue placeholder="Domain" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="domain in availableDomains" :key="domain" :value="domain">
              {{ domain }}
            </SelectItem>
          </SelectContent>
        </Select>

        <Select v-model="selectedStatus">
          <SelectTrigger class="w-[120px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="status in availableStatuses" :key="status" :value="status">
              {{ status }}
            </SelectItem>
          </SelectContent>
        </Select>

        <Button variant="outline" @click="clearFilters"> Clear Filters </Button>
      </div>
    </div>

    <!-- Results Summary -->
    <div class="flex items-center justify-between text-sm text-muted-foreground">
      <span>Showing {{ filteredAssets.length }} of {{ mockDataAssets.length }} assets</span>
      <div class="flex items-center space-x-4">
        <span>Sorted by popularity</span>
      </div>
    </div>

    <!-- Asset Grid/Table -->
    <div
      v-if="viewType === 'grid'"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
    >
      <Card
        v-for="asset in filteredAssets"
        :key="asset.id"
        class="hover:shadow-md transition-shadow cursor-pointer group"
      >
        <CardHeader class="pb-3">
          <div class="flex items-start justify-between">
            <div class="flex items-center space-x-2">
              <component :is="getAssetIcon(asset.assetType)" class="h-4 w-4" />
              <CardTitle class="text-base truncate">{{ asset.name }}</CardTitle>
            </div>
            <div class="flex items-center space-x-1">
              <Badge variant="secondary" :class="getStatusColor(asset.status)">
                {{ asset.status }}
              </Badge>
              <span :class="`font-medium ${getQualityScoreColor(asset.qualityScore)}`">
                {{ asset.qualityScore }}%
              </span>
            </div>
          </div>
          <div class="flex items-center space-x-4 text-sm text-muted-foreground">
            <span>{{ asset.assetType }}</span>
            <span>•</span>
            <span>{{ asset.domain }}</span>
          </div>
        </CardHeader>
        <CardContent class="pt-0">
          <p class="text-sm text-muted-foreground line-clamp-2 mb-3">
            {{ asset.description || 'No description available' }}
          </p>

          <div class="flex items-center justify-between text-sm text-muted-foreground mb-3">
            <div class="flex items-center space-x-1">
              <TrendingUp class="h-3 w-3" />
              <span>{{ asset.usageFrequency }}/day</span>
            </div>
            <div class="flex items-center space-x-1">
              <Star class="h-3 w-3" />
              <span>{{ asset.popularityScore }}</span>
            </div>
          </div>

          <div class="flex flex-wrap gap-1 mb-3">
            <Badge
              v-for="tag in asset.tags.slice(0, 3)"
              :key="tag"
              variant="outline"
              class="text-xs"
            >
              {{ tag }}
            </Badge>
            <Badge v-if="asset.tags.length > 3" variant="outline" class="text-xs">
              +{{ asset.tags.length - 3 }}
            </Badge>
          </div>

          <div class="flex items-center justify-between">
            <div class="text-xs text-muted-foreground">
              <div v-if="asset.owner" class="flex items-center space-x-1">
                <Users class="h-3 w-3" />
                <span>{{ asset.owner }}</span>
              </div>
            </div>
            <div class="flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button variant="ghost" size="sm" @click="openAssetDetails(asset)">
                <Eye class="h-3 w-3" />
              </Button>
              <Button
                v-if="asset.type === 'source' || asset.type === 'table'"
                variant="ghost"
                size="sm"
                @click="handleAssetNavigation(asset)"
              >
                <ExternalLink class="h-3 w-3" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Table View -->
    <Card v-else>
      <CardContent class="p-0">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="border-b">
              <tr class="text-left">
                <th class="p-4 font-medium">Asset</th>
                <th class="p-4 font-medium">Type</th>
                <th class="p-4 font-medium">Domain</th>
                <th class="p-4 font-medium">Quality</th>
                <th class="p-4 font-medium">Usage</th>
                <th class="p-4 font-medium">Owner</th>
                <th class="p-4 font-medium">Status</th>
                <th class="p-4 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="asset in filteredAssets"
                :key="asset.id"
                class="border-b hover:bg-muted/50"
              >
                <td class="p-4">
                  <div class="flex items-center space-x-2">
                    <component :is="getAssetIcon(asset.assetType)" class="h-4 w-4" />
                    <div>
                      <div class="font-medium">{{ asset.name }}</div>
                      <div class="text-sm text-muted-foreground truncate max-w-[200px]">
                        {{ asset.description }}
                      </div>
                    </div>
                  </div>
                </td>
                <td class="p-4">{{ asset.assetType }}</td>
                <td class="p-4">{{ asset.domain }}</td>
                <td class="p-4">
                  <span :class="`font-medium ${getQualityScoreColor(asset.qualityScore)}`">
                    {{ asset.qualityScore }}%
                  </span>
                </td>
                <td class="p-4">{{ asset.usageFrequency }}/day</td>
                <td class="p-4">{{ asset.owner || '-' }}</td>
                <td class="p-4">
                  <Badge :class="getStatusColor(asset.status)">
                    {{ asset.status }}
                  </Badge>
                </td>
                <td class="p-4">
                  <div class="flex space-x-1">
                    <Button variant="ghost" size="sm" @click="openAssetDetails(asset)">
                      <Eye class="h-3 w-3" />
                    </Button>
                    <Button
                      v-if="asset.type === 'source' || asset.type === 'table'"
                      variant="ghost"
                      size="sm"
                      @click="handleAssetNavigation(asset)"
                    >
                      <ExternalLink class="h-3 w-3" />
                    </Button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>

    <!-- Asset Details Sheet -->
    <Sheet :open="!!selectedAsset" @update:open="selectedAsset = null">
      <SheetContent v-if="selectedAsset" class="w-[600px] sm:w-[800px]">
        <SheetHeader>
          <SheetTitle class="flex items-center space-x-2">
            <component :is="getAssetIcon(selectedAsset.assetType)" class="h-4 w-4" />
            <span>{{ selectedAsset.name }}</span>
          </SheetTitle>
          <SheetDescription>
            {{ selectedAsset.assetType }} in {{ selectedAsset.domain }} domain
          </SheetDescription>
        </SheetHeader>

        <div class="mt-6 space-y-6">
          <!-- Basic Information -->
          <div>
            <h3 class="font-medium mb-3">Basic Information</h3>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-muted-foreground">Type:</span>
                <span class="ml-2">{{ selectedAsset.assetType }}</span>
              </div>
              <div>
                <span class="text-muted-foreground">Quality Score:</span>
                <span
                  :class="`ml-2 font-medium ${getQualityScoreColor(selectedAsset.qualityScore)}`"
                >
                  {{ selectedAsset.qualityScore }}%
                </span>
              </div>
              <div>
                <span class="text-muted-foreground">Domain:</span>
                <span class="ml-2">{{ selectedAsset.domain }}</span>
              </div>
              <div>
                <span class="text-muted-foreground">Status:</span>
                <Badge :class="`ml-2 ${getStatusColor(selectedAsset.status)}`">
                  {{ selectedAsset.status }}
                </Badge>
              </div>
              <div v-if="selectedAsset.owner">
                <span class="text-muted-foreground">Owner:</span>
                <span class="ml-2">{{ selectedAsset.owner }}</span>
              </div>
              <div v-if="selectedAsset.steward">
                <span class="text-muted-foreground">Steward:</span>
                <span class="ml-2">{{ selectedAsset.steward }}</span>
              </div>
            </div>
          </div>

          <Separator />

          <!-- Description -->
          <div v-if="selectedAsset.description">
            <h3 class="font-medium mb-3">Description</h3>
            <p class="text-sm text-muted-foreground">{{ selectedAsset.description }}</p>
          </div>

          <!-- Usage Metrics -->
          <div>
            <h3 class="font-medium mb-3">Usage Metrics</h3>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-muted-foreground">Daily Usage:</span>
                <span class="ml-2">{{ selectedAsset.usageFrequency }} queries/day</span>
              </div>
              <div>
                <span class="text-muted-foreground">Popularity Score:</span>
                <span class="ml-2">{{ selectedAsset.popularityScore }}/100</span>
              </div>
            </div>
          </div>

          <Separator />

          <!-- Tags -->
          <div>
            <h3 class="font-medium mb-3">Tags</h3>
            <div class="flex flex-wrap gap-2">
              <Badge v-for="tag in selectedAsset.tags" :key="tag" variant="outline">
                {{ tag }}
              </Badge>
            </div>
          </div>

          <!-- Lineage -->
          <div v-if="selectedAsset.type === 'table'">
            <Separator />
            <div>
              <h3 class="font-medium mb-3">Data Lineage</h3>
              <div class="space-y-2">
                <div
                  v-for="lineage in getAssetLineage(selectedAsset.id)"
                  :key="lineage.id"
                  class="text-sm border rounded p-3"
                >
                  <div class="font-medium">
                    {{ lineage.sourceTableName }} → {{ lineage.targetTableName }}
                  </div>
                  <div class="text-muted-foreground">
                    {{ lineage.transformationType }} • {{ lineage.description }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Navigation Actions -->
          <div v-if="selectedAsset.type === 'source' || selectedAsset.type === 'table'">
            <Separator />
            <div>
              <h3 class="font-medium mb-3">Actions</h3>
              <Button @click="handleAssetNavigation(selectedAsset)" class="w-full">
                View Quality Review
              </Button>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  Search,
  Database,
  Table,
  Columns,
  FileText,
  Users,
  TrendingUp,
  ExternalLink,
  Eye,
  Star
} from 'lucide-vue-next'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle
} from '@/components/ui/sheet'
import { Separator } from '@/components/ui/separator'
import type { DataAsset, CatalogFilters } from '@/types/data-quality'
import { mockDataAssets, mockDataLineage } from '@/data/mock-data'

interface DataCatalogProps {
  onSelectDataSource?: (dataSourceId: string) => void
  onSelectTable?: (dataSourceId: string, tableId: string) => void
}

const props = withDefaults(defineProps<DataCatalogProps>(), {
  onSelectDataSource: undefined,
  onSelectTable: undefined
})

const filters = ref<CatalogFilters>({
  searchTerm: '',
  assetTypes: [],
  domains: [],
  qualityScoreRange: [0, 100],
  tags: [],
  owners: [],
  status: []
})

const selectedAsset = ref<DataAsset | null>(null)
const viewType = ref<'grid' | 'table'>('grid')
const selectedAssetType = ref<string>('')
const selectedDomain = ref<string>('')
const selectedStatus = ref<string>('')

// Get unique values for filters
const availableAssetTypes = computed(() => [
  ...new Set(mockDataAssets.map((asset) => asset.assetType))
])
const availableDomains = computed(() => [...new Set(mockDataAssets.map((asset) => asset.domain))])
const availableStatuses = computed(() => [...new Set(mockDataAssets.map((asset) => asset.status))])

// Watch filter changes
const updateFilters = () => {
  filters.value.assetTypes = selectedAssetType.value ? [selectedAssetType.value] : []
  filters.value.domains = selectedDomain.value ? [selectedDomain.value] : []
  filters.value.status = selectedStatus.value ? [selectedStatus.value] : []
}

// Filter assets based on current filters
const filteredAssets = computed(() => {
  updateFilters()

  return mockDataAssets.filter((asset) => {
    // Search term filter
    if (
      filters.value.searchTerm &&
      !asset.name.toLowerCase().includes(filters.value.searchTerm.toLowerCase()) &&
      !asset.description?.toLowerCase().includes(filters.value.searchTerm.toLowerCase())
    ) {
      return false
    }

    // Asset type filter
    if (
      filters.value.assetTypes.length > 0 &&
      !filters.value.assetTypes.includes(asset.assetType)
    ) {
      return false
    }

    // Domain filter
    if (filters.value.domains.length > 0 && !filters.value.domains.includes(asset.domain)) {
      return false
    }

    // Quality score range filter
    if (
      asset.qualityScore < filters.value.qualityScoreRange[0] ||
      asset.qualityScore > filters.value.qualityScoreRange[1]
    ) {
      return false
    }

    // Tags filter
    if (
      filters.value.tags.length > 0 &&
      !filters.value.tags.some((tag) => asset.tags.includes(tag))
    ) {
      return false
    }

    // Owner filter
    if (
      filters.value.owners.length > 0 &&
      asset.owner &&
      !filters.value.owners.includes(asset.owner)
    ) {
      return false
    }

    // Status filter
    if (filters.value.status.length > 0 && !filters.value.status.includes(asset.status)) {
      return false
    }

    return true
  })
})

const getAssetIcon = (assetType: string) => {
  switch (assetType) {
    case 'database':
      return Database
    case 'table':
    case 'view':
      return Table
    case 'column':
      return Columns
    case 'file':
      return FileText
    default:
      return Database
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'good':
      return 'bg-green-100 text-green-800 border-green-200'
    case 'warning':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    case 'error':
      return 'bg-red-100 text-red-800 border-red-200'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

const getQualityScoreColor = (score: number) => {
  if (score >= 90) return 'text-green-600'
  if (score >= 70) return 'text-yellow-600'
  return 'text-red-600'
}

const handleAssetNavigation = (asset: DataAsset) => {
  if (asset.type === 'source' && props.onSelectDataSource) {
    props.onSelectDataSource(asset.id)
  } else if (asset.type === 'table' && asset.sourceId && props.onSelectTable) {
    props.onSelectTable(asset.sourceId, asset.id)
  }
}

const openAssetDetails = (asset: DataAsset) => {
  selectedAsset.value = asset
}

const clearFilters = () => {
  filters.value = {
    searchTerm: '',
    assetTypes: [],
    domains: [],
    qualityScoreRange: [0, 100],
    tags: [],
    owners: [],
    status: []
  }
  selectedAssetType.value = ''
  selectedDomain.value = ''
  selectedStatus.value = ''
}

const getAssetLineage = (assetId: string) => {
  return mockDataLineage.filter(
    (lineage) => lineage.sourceTableId === assetId || lineage.targetTableId === assetId
  )
}

// Calculate statistics
const stats = computed(() => {
  const totalAssets = mockDataAssets.length
  const totalSources = mockDataAssets.filter((asset) => asset.type === 'source').length
  const totalTables = mockDataAssets.filter((asset) => asset.type === 'table').length
  const totalFields = mockDataAssets.filter((asset) => asset.type === 'field').length
  const avgQualityScore = Math.round(
    mockDataAssets.reduce((sum, asset) => sum + asset.qualityScore, 0) / totalAssets
  )
  const totalDailyUsage = mockDataAssets.reduce((sum, asset) => sum + asset.usageFrequency, 0)

  return {
    totalAssets,
    totalSources,
    totalTables,
    totalFields,
    avgQualityScore,
    totalDailyUsage
  }
})

// Popular assets
const popularAssets = computed(() =>
  mockDataAssets
    .filter((asset) => asset.type !== 'field')
    .sort((a, b) => b.popularityScore - a.popularityScore)
    .slice(0, 3)
)

// Recent assets
const recentAssets = computed(() =>
  mockDataAssets.filter((asset) => asset.type !== 'field').slice(0, 3)
)
</script>
