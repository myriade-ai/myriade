<template>
  <div class="space-y-6">
    <div class="text-center space-y-2">
      <h1 class="text-3xl font-bold">Semantic Layer</h1>
      <p class="text-muted-foreground">
        Understand your data through business definitions, relationships, and lineage
      </p>
    </div>

    <Tabs default-value="glossary" class="w-full">
      <TabsList class="grid w-full grid-cols-3">
        <TabsTrigger value="glossary">Business Glossary</TabsTrigger>
        <TabsTrigger value="relationships">Data Relationships</TabsTrigger>
        <TabsTrigger value="lineage">Data Lineage</TabsTrigger>
      </TabsList>

      <TabsContent value="glossary" class="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center space-x-2">
              <BookOpen class="w-5 h-5" />
              <span>Business Glossary</span>
            </CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <!-- Search and Filter -->
            <div class="flex space-x-4">
              <div class="flex-1 relative">
                <Search
                  class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground"
                />
                <Input
                  v-model="searchTerm"
                  placeholder="Search terms and definitions..."
                  class="pl-10"
                />
              </div>
              <div class="flex space-x-2">
                <Badge
                  v-for="category in categories"
                  :key="category"
                  :variant="selectedCategory === category ? 'default' : 'outline'"
                  class="cursor-pointer"
                  @click="selectedCategory = category"
                >
                  {{ category === 'all' ? 'All Categories' : category }}
                </Badge>
              </div>
            </div>

            <!-- Glossary Terms -->
            <ScrollArea class="h-[500px]">
              <div class="space-y-4">
                <Card v-for="term in filteredGlossary" :key="term.id" class="p-4">
                  <div class="space-y-3">
                    <div class="flex items-start justify-between">
                      <div class="flex items-start space-x-3">
                        <div>
                          <div class="flex items-center space-x-2 mb-1">
                            <h3 class="font-semibold text-lg">{{ term.term }}</h3>
                            <component
                              v-if="getTermQualityInfo(term).qualityScore !== null"
                              :is="getQualityIcon(getTermQualityInfo(term).status)"
                            />
                          </div>
                          <div class="flex items-center space-x-2">
                            <Badge :class="getCategoryColor(term.category)">
                              {{ term.category }}
                            </Badge>
                            <Badge
                              v-if="getTermQualityInfo(term).qualityScore !== null"
                              :class="getQualityBadgeColor(getTermQualityInfo(term).status)"
                            >
                              Quality: {{ getTermQualityInfo(term).qualityScore }}%
                            </Badge>
                          </div>
                        </div>
                      </div>
                      <div v-if="getTermQualityInfo(term).qualityScore !== null" class="text-right">
                        <div class="flex items-center space-x-2 mb-1">
                          <span class="text-sm text-muted-foreground"
                            >{{ getTermQualityInfo(term).relatedFieldsCount }} fields</span
                          >
                        </div>
                        <div class="w-24">
                          <Progress :value="getTermQualityInfo(term).qualityScore" class="h-2" />
                        </div>
                        <p
                          v-if="getTermQualityInfo(term).issuesCount > 0"
                          class="text-xs text-red-600 mt-1"
                        >
                          {{ getTermQualityInfo(term).issuesCount }} issues
                        </p>
                      </div>
                    </div>

                    <p class="text-muted-foreground">{{ term.definition }}</p>

                    <div
                      v-if="
                        getTermQualityInfo(term).qualityScore !== null &&
                        getTermQualityInfo(term).issuesCount > 0
                      "
                      class="p-3 bg-yellow-50 border border-yellow-200 rounded text-sm"
                    >
                      <p class="font-medium text-yellow-800">Data Quality Impact</p>
                      <p class="text-yellow-700">
                        This business concept has {{ getTermQualityInfo(term).issuesCount }} data
                        quality issues across
                        {{ getTermQualityInfo(term).relatedFieldsCount }} related fields. This may
                        affect business processes that rely on accurate
                        {{ term.term.toLowerCase() }} data.
                      </p>
                    </div>

                    <div v-if="term.examples && term.examples.length > 0">
                      <h4 class="font-medium text-sm mb-2">Examples:</h4>
                      <ul class="text-sm text-muted-foreground space-y-1">
                        <li
                          v-for="(example, index) in term.examples"
                          :key="index"
                          class="flex items-start space-x-2"
                        >
                          <span class="text-blue-600 mt-1">•</span>
                          <span>{{ example }}</span>
                        </li>
                      </ul>
                    </div>

                    <div v-if="term.relatedTerms.length > 0">
                      <h4 class="font-medium text-sm mb-2">Related Terms:</h4>
                      <div class="flex flex-wrap gap-2">
                        <Badge
                          v-for="(relatedTerm, index) in term.relatedTerms"
                          :key="index"
                          variant="secondary"
                          class="text-xs"
                        >
                          <Tag class="w-3 h-3 mr-1" />
                          {{ relatedTerm }}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="relationships" class="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center space-x-2">
              <Network class="w-5 h-5" />
              <span>Data Relationships</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea class="h-[500px]">
              <div class="space-y-4">
                <Card
                  v-for="relationship in mockSemanticRelationships"
                  :key="relationship.id"
                  class="p-4"
                >
                  <div class="flex items-center space-x-4">
                    <div class="flex-shrink-0">
                      <component :is="getRelationshipIcon(relationship.type)" />
                    </div>

                    <div class="flex-1">
                      <div class="flex items-center space-x-2 mb-2">
                        <Badge :class="getRelationshipColor(relationship.type)">
                          {{ relationship.type.replace('_', ' ') }}
                        </Badge>
                      </div>

                      <div class="flex items-center space-x-2 text-sm">
                        <div class="flex items-center space-x-1">
                          <TableIcon class="w-4 h-4" />
                          <span class="font-mono">{{
                            getTableName(relationship.fromTableId)
                          }}</span>
                          <template
                            v-if="getFieldName(relationship.fromTableId, relationship.fromFieldId)"
                          >
                            <span>.</span>
                            <span class="font-mono text-blue-600">{{
                              getFieldName(relationship.fromTableId, relationship.fromFieldId)
                            }}</span>
                          </template>
                        </div>

                        <ArrowRight class="w-4 h-4 text-muted-foreground" />

                        <div class="flex items-center space-x-1">
                          <TableIcon class="w-4 h-4" />
                          <span class="font-mono">{{ getTableName(relationship.toTableId) }}</span>
                          <template
                            v-if="getFieldName(relationship.toTableId, relationship.toFieldId)"
                          >
                            <span>.</span>
                            <span class="font-mono text-blue-600">{{
                              getFieldName(relationship.toTableId, relationship.toFieldId)
                            }}</span>
                          </template>
                        </div>
                      </div>

                      <p class="text-sm text-muted-foreground mt-2">
                        {{ relationship.description }}
                      </p>
                    </div>
                  </div>
                </Card>
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="lineage" class="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center space-x-2">
              <GitBranch class="w-5 h-5" />
              <span>Data Lineage</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div class="text-center py-8 text-muted-foreground">
              <GitBranch class="w-12 h-12 mx-auto mb-4 opacity-50" />
              <h3 class="font-medium mb-2">Data Lineage Visualization</h3>
              <p class="text-sm max-w-md mx-auto">
                Interactive data lineage visualization would show how data flows through your
                systems, from source to destination, including transformations and dependencies.
              </p>
              <div class="mt-6 p-4 bg-muted rounded-lg">
                <p class="text-sm">
                  <strong>Future Enhancement:</strong> This section would include an interactive
                  graph showing data flow paths, transformation points, and impact analysis for data
                  changes.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  </div>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { mockBusinessGlossary, mockDataSources, mockSemanticRelationships } from '@/data/mock-data'
import type { BusinessGlossary, DataField } from '@/types/data-quality'
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  BookOpen,
  CheckCircle,
  GitBranch,
  Link,
  Network,
  Search,
  Table as TableIcon,
  Tag,
  Target,
  XCircle
} from 'lucide-vue-next'
import { computed, ref } from 'vue'

const searchTerm = ref('')
const selectedCategory = ref<string>('all')

const getRelationshipIcon = (type: string) => {
  switch (type) {
    case 'foreign_key':
      return Link
    case 'business_hierarchy':
      return GitBranch
    case 'derived_from':
      return ArrowRight
    case 'aggregates_to':
      return Target
    default:
      return Network
  }
}

const getRelationshipColor = (type: string) => {
  switch (type) {
    case 'foreign_key':
      return 'bg-blue-100 text-blue-800'
    case 'business_hierarchy':
      return 'bg-green-100 text-green-800'
    case 'derived_from':
      return 'bg-purple-100 text-purple-800'
    case 'aggregates_to':
      return 'bg-orange-100 text-orange-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const getCategoryColor = (category: string) => {
  switch (category) {
    case 'Core Business':
      return 'bg-blue-100 text-blue-800'
    case 'Financial':
      return 'bg-green-100 text-green-800'
    case 'Data Privacy':
      return 'bg-red-100 text-red-800'
    case 'Technical':
      return 'bg-purple-100 text-purple-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const filteredGlossary = computed(() => {
  return mockBusinessGlossary.filter((term) => {
    const matchesSearch =
      term.term.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
      term.definition.toLowerCase().includes(searchTerm.value.toLowerCase())
    const matchesCategory =
      selectedCategory.value === 'all' || term.category === selectedCategory.value
    return matchesSearch && matchesCategory
  })
})

const categories = computed(() => [
  'all',
  ...Array.from(new Set(mockBusinessGlossary.map((term) => term.category)))
])

// Helper function to calculate quality metrics for business terms
const getTermQualityInfo = (term: BusinessGlossary) => {
  const relatedFields: DataField[] = []
  let totalIssues = 0

  // Find fields related to this business term by matching tags/names
  for (const source of mockDataSources) {
    for (const table of source.tables) {
      for (const field of table.fields) {
        // Check if field is related to this business term
        const termLower = term.term.toLowerCase()
        const fieldNameLower = field.name.toLowerCase()
        const fieldTags = field.tags.map((tag) => tag.toLowerCase())

        if (
          fieldNameLower.includes(termLower) ||
          fieldTags.some((tag) => tag.includes(termLower)) ||
          term.relatedTerms.some(
            (related) =>
              fieldNameLower.includes(related.toLowerCase()) ||
              fieldTags.some((tag) => tag.includes(related.toLowerCase()))
          )
        ) {
          relatedFields.push(field)
          totalIssues += field.issuesCount
        }
      }
    }
  }

  if (relatedFields.length === 0) {
    return { qualityScore: null, issuesCount: 0, relatedFieldsCount: 0, status: 'unknown' as const }
  }

  const avgQualityScore = Math.round(
    relatedFields.reduce((sum, field) => sum + field.qualityScore, 0) / relatedFields.length
  )

  const status = avgQualityScore >= 90 ? 'good' : avgQualityScore >= 70 ? 'warning' : 'error'

  return {
    qualityScore: avgQualityScore,
    issuesCount: totalIssues,
    relatedFieldsCount: relatedFields.length,
    status
  }
}

const getQualityIcon = (status: string) => {
  switch (status) {
    case 'good':
      return CheckCircle
    case 'warning':
      return AlertTriangle
    case 'error':
      return XCircle
    default:
      return BarChart3
  }
}

const getQualityBadgeColor = (status: string) => {
  switch (status) {
    case 'good':
      return 'bg-green-100 text-green-800'
    case 'warning':
      return 'bg-yellow-100 text-yellow-800'
    case 'error':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

// Helper function to find table names by ID
const getTableName = (tableId: string) => {
  for (const source of mockDataSources) {
    const table = source.tables.find((t) => t.id === tableId)
    if (table) return table.name
  }
  return 'Unknown Table'
}

const getFieldName = (tableId: string, fieldId?: string) => {
  if (!fieldId) return null
  for (const source of mockDataSources) {
    const table = source.tables.find((t) => t.id === tableId)
    if (table) {
      const field = table.fields.find((f) => f.id === fieldId)
      if (field) return field.name
    }
  }
  return 'Unknown Field'
}
</script>
