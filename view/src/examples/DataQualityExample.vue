<template>
  <div class="container mx-auto p-6">
    <h1 class="text-3xl font-bold mb-6">Data Quality Review Example</h1>

    <!-- Example 1: Full Dashboard -->
    <div class="mb-8">
      <h2 class="text-2xl font-semibold mb-4">Complete Dashboard</h2>
      <DataQualityDashboard />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Example 2: Standalone Review Component -->
      <div>
        <h2 class="text-2xl font-semibold mb-4">Quality Review Component</h2>
        <DataQualityReview :data="sampleData" :columns="sampleColumns" />
      </div>

      <!-- Example 3: Profiling Summary -->
      <div>
        <h2 class="text-2xl font-semibold mb-4">Profiling Summary</h2>
        <DataProfilingSummary :data="profilingData" />
      </div>
    </div>

    <!-- Example 4: Using the Composable -->
    <div class="mt-8">
      <h2 class="text-2xl font-semibold mb-4">Interactive Analysis</h2>
      <Card>
        <CardHeader>
          <CardTitle>Analyze Your Data</CardTitle>
          <CardDescription> Upload or analyze sample data to see quality metrics </CardDescription>
        </CardHeader>
        <CardContent>
          <div class="space-y-4">
            <div class="flex space-x-4">
              <button
                @click="analyzeSampleData"
                :disabled="isAnalyzing"
                class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
              >
                {{ isAnalyzing ? 'Analyzing...' : 'Analyze Sample Data' }}
              </button>

              <button
                @click="generateDemoReport"
                class="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/90"
              >
                Generate Report
              </button>
            </div>

            <div v-if="analysisResults" class="space-y-4">
              <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div v-for="(value, key) in analysisResults" :key="key" class="text-center">
                  <div class="text-2xl font-bold">{{ value }}%</div>
                  <div class="text-sm text-muted-foreground capitalize">{{ key }}</div>
                </div>
              </div>

              <div class="mt-4">
                <h4 class="font-medium mb-2">Quality Score: {{ overallQualityScore }}%</h4>
                <Progress :model-value="overallQualityScore" />
              </div>
            </div>

            <div v-if="report" class="mt-6 p-4 border rounded-lg">
              <h4 class="font-medium mb-2">Report Summary</h4>
              <p class="text-sm text-muted-foreground mb-4">
                Overall Score: {{ report.overallScore }}% | Total Issues: {{ report.totalIssues }} |
                High Priority: {{ report.highSeverityIssues }}
              </p>
              <div v-if="report.recommendations.length">
                <h5 class="font-medium mb-2">Recommendations:</h5>
                <ul class="list-disc list-inside space-y-1">
                  <li v-for="rec in report.recommendations" :key="rec" class="text-sm">
                    {{ rec }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  DataProfilingSummary,
  DataQualityDashboard,
  DataQualityReview
} from '@/components/data-quality'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { useDataQuality } from '@/composables/useDataQuality'
import { ref } from 'vue'

// Sample data for demonstration
const sampleData = ref([
  {
    id: 1,
    name: 'John Doe',
    email: 'john@example.com',
    phone: '555-0123',
    created_at: '2024-01-01'
  },
  {
    id: 2,
    name: 'Jane Smith',
    email: 'jane@example.com',
    phone: '5550124',
    created_at: '2024-01-02'
  },
  { id: 3, name: '', email: 'invalid-email', phone: null, created_at: '2024-01-03' },
  {
    id: 4,
    name: 'Bob Johnson',
    email: 'bob@example.com',
    phone: '555-0125',
    created_at: 'invalid-date'
  },
  {
    id: 1,
    name: 'John Doe',
    email: 'john@example.com',
    phone: '555-0123',
    created_at: '2024-01-01'
  } // duplicate
])

const sampleColumns = ref(['id', 'name', 'email', 'phone', 'created_at'])

const profilingData = ref({
  rowCount: 1250,
  columnCount: 5,
  duplicateRows: 23,
  missingValues: 187
})

// Using the composable
const { isAnalyzing, analysisResults, overallQualityScore, analyzeDataQuality, generateReport } =
  useDataQuality()

const report = ref(null)

const analyzeSampleData = async () => {
  await analyzeDataQuality(sampleData.value, sampleColumns.value)
}

const generateDemoReport = () => {
  report.value = generateReport()
}
</script>
