<template>
  <div class="min-h-screen bg-background">
    <div class="container mx-auto px-4 py-8">
      <component :is="renderCurrentView()" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, h } from 'vue'
import DataQualityDashboard from '@/components/DataQualityDashboard.vue'
import DataQualityReview from '@/components/DataQualityReview.vue'
import TableQualityReview from '@/components/TableQualityReview.vue'
import FieldQualityReview from '@/components/FieldQualityReview.vue'
import SemanticLayer from '@/components/SemanticLayer.vue'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { DataSource, DataTable, DataField } from '@/types/data-quality'
import { mockDataSources, mockQualityIssues } from '@/data/mock-data'

type ViewType = 'dashboard' | 'source-review' | 'table-review' | 'field-review'

const currentView = ref<ViewType>('dashboard')
const selectedDataSource = ref<DataSource | null>(null)
const selectedTable = ref<DataTable | null>(null)
const selectedField = ref<DataField | null>(null)

const handleSelectDataSource = (dataSource: DataSource) => {
  selectedDataSource.value = dataSource
  selectedTable.value = null
  selectedField.value = null
  currentView.value = 'source-review'
}

const handleSelectTable = (dataSource: DataSource, tableId: string) => {
  const table = dataSource.tables.find(t => t.id === tableId)
  if (table) {
    selectedDataSource.value = dataSource
    selectedTable.value = table
    selectedField.value = null
    currentView.value = 'table-review'
  }
}

const handleSelectField = (fieldId: string) => {
  if (selectedTable.value) {
    const field = selectedTable.value.fields.find(f => f.id === fieldId)
    if (field) {
      selectedField.value = field
      currentView.value = 'field-review'
    }
  }
}

const handleBackToDashboard = () => {
  currentView.value = 'dashboard'
  selectedDataSource.value = null
  selectedTable.value = null
  selectedField.value = null
}

const handleBackToSource = () => {
  currentView.value = 'source-review'
  selectedTable.value = null
  selectedField.value = null
}

const handleBackToTable = () => {
  currentView.value = 'table-review'
  selectedField.value = null
}

const renderCurrentView = () => {
  switch (currentView.value) {
    case 'dashboard':
      return h('div', { class: 'space-y-6' }, [
        h('div', { class: 'text-center space-y-2' }, [
          h('h1', { class: 'text-3xl font-bold' }, 'Data Quality Platform'),
          h('p', { class: 'text-muted-foreground' }, 
            'Review and improve your data quality with AI-powered insights'
          )
        ]),
        h(Tabs, { defaultValue: 'overview', class: 'w-full' }, {
          default: () => [
            h(TabsList, { class: 'grid w-full grid-cols-2' }, {
              default: () => [
                h(TabsTrigger, { value: 'overview' }, () => 'Data Quality Overview'),
                h(TabsTrigger, { value: 'semantic' }, () => 'Semantic Layer')
              ]
            }),
            h(TabsContent, { value: 'overview' }, {
              default: () => h(DataQualityDashboard, {
                onSelectDataSource: handleSelectDataSource,
                onSelectTable: handleSelectTable
              })
            }),
            h(TabsContent, { value: 'semantic' }, {
              default: () => h(SemanticLayer)
            })
          ]
        })
      ])

    case 'source-review':
      return selectedDataSource.value ? h(DataQualityReview, {
        dataSource: selectedDataSource.value,
        onBack: handleBackToDashboard,
        onSelectTable: (tableId: string) => handleSelectTable(selectedDataSource.value!, tableId)
      }) : null

    case 'table-review':
      return selectedTable.value ? h(TableQualityReview, {
        table: selectedTable.value,
        issues: mockQualityIssues,
        onBack: handleBackToSource,
        onSelectField: handleSelectField
      }) : null

    case 'field-review':
      return selectedField.value && selectedTable.value ? h(FieldQualityReview, {
        field: selectedField.value,
        tableName: selectedTable.value.name,
        issues: mockQualityIssues,
        onBack: handleBackToTable
      }) : null

    default:
      return null
  }
}
</script>