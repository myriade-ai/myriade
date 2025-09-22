<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <Button variant="ghost" size="sm" @click="onBack">
          <ArrowLeft class="w-4 h-4 mr-2" />
          Back to Table
        </Button>
        <div class="flex items-center space-x-2">
          <Database class="w-5 h-5" />
          <div>
            <div class="flex items-center space-x-2">
              <h1 class="font-mono">{{ field.name }}</h1>
              <Key v-if="field.isKey" class="w-4 h-4 text-blue-600" />
              <Shield v-if="field.isSensitive" class="w-4 h-4 text-red-600" />
            </div>
            <p class="text-muted-foreground">{{ tableName }} • {{ field.dataType }}</p>
          </div>
        </div>
      </div>
      <div class="flex items-center space-x-2">
        <component :is="getStatusIcon(field.status)" />
        <Badge
          :class="
            field.qualityScore >= 90
              ? 'bg-green-100 text-green-800'
              : field.qualityScore >= 70
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
          "
        >
          Quality Score: {{ field.qualityScore }}%
        </Badge>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Main Content -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Business Context -->
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center space-x-2">
              <BookOpen class="w-4 h-4" />
              <span>Business Definition & Rules</span>
            </CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div>
              <h4 class="font-medium mb-2">Definition</h4>
              <p class="text-sm text-muted-foreground">
                {{ field.businessDefinition || 'No business definition provided' }}
              </p>
            </div>

            <div v-if="field.businessRules && field.businessRules.length > 0">
              <h4 class="font-medium mb-2">Business Rules</h4>
              <ul class="text-sm text-muted-foreground space-y-1">
                <li
                  v-for="(rule, index) in field.businessRules"
                  :key="index"
                  class="flex items-start space-x-2"
                >
                  <span class="text-blue-600 mt-1">•</span>
                  <span>{{ rule }}</span>
                </li>
              </ul>
            </div>

            <div>
              <h4 class="font-medium mb-2">Tags</h4>
              <div class="flex flex-wrap gap-2">
                <Badge v-for="tag in field.tags" :key="tag" variant="secondary" class="text-xs">
                  <Tag class="w-3 h-3 mr-1" />
                  {{ tag }}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Quality Metrics -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle class="flex items-center space-x-2">
                <BarChart3 class="w-4 h-4" />
                <span>Completeness</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-sm">Non-null values</span>
                  <span class="text-sm font-medium">{{ 100 - field.nullPercentage }}%</span>
                </div>
                <Progress :value="100 - field.nullPercentage" />
                <p class="text-xs text-muted-foreground">
                  {{ field.nullPercentage }}% of values are missing or null
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle class="flex items-center space-x-2">
                <BarChart3 class="w-4 h-4" />
                <span>Uniqueness</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-sm">Unique values</span>
                  <span class="text-sm font-medium">{{ field.uniquePercentage }}%</span>
                </div>
                <Progress :value="field.uniquePercentage" />
                <p class="text-xs text-muted-foreground">
                  {{ 100 - field.uniquePercentage }}% are duplicate values
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- Quality Issues -->
        <Card v-if="fieldIssues.length > 0">
          <CardHeader>
            <CardTitle>Quality Issues</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="space-y-4">
              <div v-for="issue in fieldIssues" :key="issue.id" class="p-4 border rounded-lg">
                <div class="flex items-center justify-between mb-2">
                  <h4 class="font-medium">{{ issue.description }}</h4>
                  <Badge :class="getSeverityColor(issue.severity)">
                    {{ issue.severity }}
                  </Badge>
                </div>
                <p class="text-sm text-muted-foreground mb-2">
                  {{ issue.affectedRows }} rows affected
                </p>
                <p class="text-sm mb-2">{{ issue.suggestion }}</p>
                <div v-if="issue.businessImpact" class="p-3 bg-blue-50 rounded text-sm">
                  <strong>Business Impact:</strong> {{ issue.businessImpact }}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Data Samples -->
        <Card>
          <CardHeader>
            <CardTitle>Data Samples</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="space-y-2">
              <div
                v-for="(sample, index) in mockFieldSamples"
                :key="index"
                :class="`p-2 rounded text-sm font-mono ${
                  sample.issues.length > 0 ? 'bg-red-50 border border-red-200' : 'bg-gray-50'
                }`"
              >
                <div class="flex items-center justify-between">
                  <span
                    :class="
                      sample.value === '' || sample.value === 'NULL'
                        ? 'text-muted-foreground italic'
                        : ''
                    "
                  >
                    {{ sample.value === '' ? '(empty)' : sample.value }}
                  </span>
                  <div v-if="sample.issues.length > 0" class="flex space-x-1">
                    <Badge
                      v-for="(issue, issueIndex) in sample.issues"
                      :key="issueIndex"
                      variant="destructive"
                      class="text-xs"
                    >
                      {{ issue.replace('_', ' ') }}
                    </Badge>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- AI Chat Sidebar -->
      <div class="space-y-4">
        <Card class="h-[600px] flex flex-col">
          <CardHeader>
            <CardTitle class="flex items-center space-x-2">
              <Bot class="w-5 h-5" />
              <span>Field Quality Agent</span>
            </CardTitle>
          </CardHeader>
          <CardContent class="flex-1 flex flex-col p-0">
            <ScrollArea class="flex-1 p-4">
              <div class="space-y-4">
                <div
                  v-for="message in chatMessages"
                  :key="message.id"
                  :class="`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`"
                >
                  <div
                    :class="`max-w-[80%] rounded-lg p-3 ${
                      message.type === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'
                    }`"
                  >
                    <div class="flex items-center space-x-2 mb-1">
                      <Bot v-if="message.type === 'agent'" class="w-4 h-4" />
                      <User v-else class="w-4 h-4" />
                      <span class="text-xs opacity-70">{{ message.timestamp }}</span>
                    </div>
                    <p class="text-sm">{{ message.content }}</p>
                  </div>
                </div>
              </div>
            </ScrollArea>
            <Separator />
            <div class="p-4">
              <div class="flex space-x-2">
                <Input
                  v-model="newMessage"
                  placeholder="Ask about field quality..."
                  @keypress="(e) => e.key === 'Enter' && sendMessage()"
                />
                <Button size="sm" @click="sendMessage">
                  <Send class="w-4 h-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import {
  ArrowLeft,
  Send,
  Bot,
  User,
  Database,
  Key,
  Shield,
  Tag,
  BookOpen,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-vue-next'
import type { DataField, QualityIssue, ChatMessage } from '@/types/data-quality'

interface Props {
  field: DataField
  tableName: string
  issues: QualityIssue[]
  onBack: () => void
}

const props = defineProps<Props>()

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'high':
      return 'bg-red-100 text-red-800'
    case 'medium':
      return 'bg-yellow-100 text-yellow-800'
    case 'low':
      return 'bg-blue-100 text-blue-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

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

// Mock sample data for the field
const mockFieldSamples = [
  { value: 'john.doe@example.com', issues: [] },
  { value: '', issues: ['missing_value'] },
  { value: 'jane@company.com', issues: [] },
  { value: 'invalid-email', issues: ['invalid_format'] },
  { value: 'alice.brown@test.org', issues: [] },
  { value: 'bob@domain', issues: ['invalid_format'] },
  { value: 'sarah.wilson@example.com', issues: [] },
  { value: 'NULL', issues: ['missing_value'] }
]

const fieldIssues = computed(() => props.issues.filter((issue) => issue.fieldId === props.field.id))

const chatMessages = ref<ChatMessage[]>([
  {
    id: '1',
    type: 'agent',
    content: `I'm analyzing the "${props.field.name}" field in the ${props.tableName} table. This field has a quality score of ${props.field.qualityScore}% with ${props.field.issuesCount} issues. Based on its business definition: "${props.field.businessDefinition}", let me help you understand the quality concerns and their business impact.`,
    timestamp: '10:30 AM',
    context: {
      level: 'field',
      entityId: props.field.id,
      entityName: props.field.name
    }
  }
])

const newMessage = ref('')

const sendMessage = () => {
  if (!newMessage.value.trim()) return

  const userMessage: ChatMessage = {
    id: Date.now().toString(),
    type: 'user',
    content: newMessage.value,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    context: {
      level: 'field',
      entityId: props.field.id,
      entityName: props.field.name
    }
  }

  chatMessages.value.push(userMessage)
  newMessage.value = ''

  // Simulate AI response with field-specific context
  setTimeout(() => {
    const agentMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      type: 'agent',
      content: `Given that "${props.field.name}" is ${props.field.isSensitive ? 'sensitive data (PII)' : 'non-sensitive'} with ${props.field.nullPercentage}% null values, I recommend focusing on ${props.field.issuesCount > 0 ? 'the data quality issues that could impact business operations' : 'maintaining the current high quality standards'}. Let me provide specific recommendations.`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      context: {
        level: 'field',
        entityId: props.field.id,
        entityName: props.field.name
      }
    }
    chatMessages.value.push(agentMessage)
  }, 1000)
}
</script>
