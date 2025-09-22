<template>
  <div class="space-y-6">
    <!-- Overview Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Data Sources</CardTitle>
          <Database class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ mockDataSources.length }}</div>
          <p class="text-xs text-muted-foreground">Active connections</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Avg Quality Score</CardTitle>
          <TrendingUp class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div :class="`text-2xl font-bold ${getQualityColor(avgQualityScore)}`">
            {{ avgQualityScore }}%
          </div>
          <p class="text-xs text-muted-foreground">Across all sources</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Total Records</CardTitle>
          <TrendingUp class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{{ totalRecords.toLocaleString() }}</div>
          <p class="text-xs text-muted-foreground">Data points analyzed</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">Quality Issues</CardTitle>
          <TrendingDown class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold text-red-600">{{ totalIssues }}</div>
          <p class="text-xs text-muted-foreground">Require attention</p>
        </CardContent>
      </Card>
    </div>

    <!-- Data Sources List -->
    <div class="space-y-4">
      <h2>Data Sources</h2>
      <div class="space-y-4">
        <Card
          v-for="dataSource in mockDataSources"
          :key="dataSource.id"
          class="hover:shadow-md transition-shadow"
        >
          <CardContent class="p-6">
            <Collapsible
              :open="expandedSources.has(dataSource.id)"
              @update:open="toggleSourceExpansion(dataSource.id)"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4 flex-1">
                  <CollapsibleTrigger as-child>
                    <Button variant="ghost" size="sm" class="p-0">
                      <ChevronDown v-if="expandedSources.has(dataSource.id)" class="w-4 h-4" />
                      <ChevronRight v-else class="w-4 h-4" />
                    </Button>
                  </CollapsibleTrigger>
                  <div class="flex items-center space-x-2">
                    <component :is="getStatusIcon(dataSource.status)" />
                    <div>
                      <h3 class="font-medium">{{ dataSource.name }}</h3>
                      <p class="text-sm text-muted-foreground">
                        {{ dataSource.type }} •
                        {{ dataSource.recordCount.toLocaleString() }} records •
                        {{ dataSource.tables.length }} tables
                      </p>
                    </div>
                  </div>
                </div>

                <div class="flex items-center space-x-4">
                  <div class="text-right">
                    <div class="flex items-center space-x-2">
                      <span class="text-sm">Quality Score:</span>
                      <Badge :class="getQualityBadgeColor(dataSource.qualityScore)">
                        {{ dataSource.qualityScore }}%
                      </Badge>
                    </div>
                    <div class="mt-2">
                      <Progress :value="dataSource.qualityScore" class="w-32" />
                    </div>
                  </div>

                  <div class="text-right">
                    <p class="text-sm font-medium">{{ dataSource.issuesCount }} issues</p>
                    <p class="text-xs text-muted-foreground">
                      Updated {{ dataSource.lastUpdated }}
                    </p>
                  </div>

                  <Button variant="outline" size="sm" @click="onSelectDataSource(dataSource)">
                    Review Source
                  </Button>
                </div>
              </div>

              <CollapsibleContent class="mt-4">
                <div class="ml-8 space-y-2">
                  <div
                    v-for="table in dataSource.tables"
                    :key="table.id"
                    class="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 cursor-pointer"
                    @click="onSelectTable(dataSource, table.id)"
                  >
                    <div class="flex items-center space-x-3">
                      <TableIcon class="w-4 h-4 text-muted-foreground" />
                      <div>
                        <h4 class="font-medium text-sm">{{ table.name }}</h4>
                        <p class="text-xs text-muted-foreground">
                          {{ table.recordCount.toLocaleString() }} records •
                          {{ table.fields.length }} fields
                        </p>
                      </div>
                    </div>

                    <div class="flex items-center space-x-3">
                      <div class="text-right">
                        <Badge
                          :class="getQualityBadgeColor(table.qualityScore)"
                          variant="secondary"
                        >
                          {{ table.qualityScore }}%
                        </Badge>
                      </div>

                      <div class="text-right">
                        <p class="text-xs font-medium">{{ table.issuesCount }} issues</p>
                      </div>

                      <Button variant="ghost" size="sm"> Review Table </Button>
                    </div>
                  </div>
                </div>
              </CollapsibleContent>
            </Collapsible>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Progress } from '@/components/ui/progress'
import { mockDataSources } from '@/data/mock-data'
import type { DataSource } from '@/types/data-quality'
import {
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Database,
  Table as TableIcon,
  TrendingDown,
  TrendingUp,
  XCircle
} from 'lucide-vue-next'
import { computed, ref } from 'vue'

interface Props {
  onSelectDataSource: (dataSource: DataSource) => void
  onSelectTable: (dataSource: DataSource, tableId: string) => void
}

defineProps<Props>()

const expandedSources = ref(new Set<string>())

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'good':
      return CheckCircle
    case 'warning':
      return AlertTriangle
    case 'error':
      return XCircle
    default:
      return Database
  }
}

const getQualityColor = (score: number) => {
  if (score >= 90) return 'text-green-600'
  if (score >= 70) return 'text-yellow-600'
  return 'text-red-600'
}

const getQualityBadgeColor = (score: number) => {
  if (score >= 90) return 'bg-green-100 text-green-800'
  if (score >= 70) return 'bg-yellow-100 text-yellow-800'
  return 'bg-red-100 text-red-800'
}

const avgQualityScore = computed(() =>
  Math.round(mockDataSources.reduce((sum, ds) => sum + ds.qualityScore, 0) / mockDataSources.length)
)

const totalRecords = computed(() => mockDataSources.reduce((sum, ds) => sum + ds.recordCount, 0))

const totalIssues = computed(() => mockDataSources.reduce((sum, ds) => sum + ds.issuesCount, 0))

const toggleSourceExpansion = (sourceId: string) => {
  const newExpanded = new Set(expandedSources.value)
  if (newExpanded.has(sourceId)) {
    newExpanded.delete(sourceId)
  } else {
    newExpanded.add(sourceId)
  }
  expandedSources.value = newExpanded
}
</script>
