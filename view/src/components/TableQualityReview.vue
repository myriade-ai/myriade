<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <Button variant="ghost" size="sm" @click="onBack">
          <ArrowLeft class="w-4 h-4 mr-2" />
          Back to Source
        </Button>
        <div class="flex items-center space-x-2">
          <TableIcon class="w-5 h-5" />
          <div>
            <h1>{{ table.name }}</h1>
            <p class="text-muted-foreground">{{ table.recordCount.toLocaleString() }} records • {{ table.fields.length }} fields</p>
          </div>
        </div>
      </div>
      <Badge :class="table.qualityScore >= 90 ? 'bg-green-100 text-green-800' : table.qualityScore >= 70 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'">
        Quality Score: {{ table.qualityScore }}%
      </Badge>
    </div>

    <!-- Business Context -->
    <Card v-if="table.businessDefinition">
      <CardHeader>
        <CardTitle class="flex items-center space-x-2">
          <BookOpen class="w-4 h-4" />
          <span>Business Definition</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p class="mb-3">{{ table.businessDefinition }}</p>
        <div class="flex flex-wrap gap-2">
          <Badge 
            v-for="tag in table.tags" 
            :key="tag" 
            variant="secondary" 
            class="text-xs"
          >
            <Tag class="w-3 h-3 mr-1" />
            {{ tag }}
          </Badge>
        </div>
      </CardContent>
    </Card>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Main Content -->
      <div class="lg:col-span-2 space-y-6">
        <Tabs default-value="fields" class="w-full">
          <TabsList class="grid w-full grid-cols-4">
            <TabsTrigger value="fields">Fields Overview</TabsTrigger>
            <TabsTrigger value="data">Data Preview</TabsTrigger>
            <TabsTrigger value="issues">Quality Issues</TabsTrigger>
            <TabsTrigger value="metrics">Quality Metrics</TabsTrigger>
          </TabsList>
          
          <TabsContent value="fields" class="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Fields in {{ table.name }}</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Field Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Quality Score</TableHead>
                      <TableHead>Issues</TableHead>
                      <TableHead>Properties</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow v-for="field in table.fields" :key="field.id">
                      <TableCell>
                        <div class="flex items-center space-x-2">
                          <span class="font-mono">{{ field.name }}</span>
                          <Key v-if="field.isKey" class="w-3 h-3 text-blue-600" />
                          <Shield v-if="field.isSensitive" class="w-3 h-3 text-red-600" />
                        </div>
                      </TableCell>
                      <TableCell class="font-mono text-sm">{{ field.dataType }}</TableCell>
                      <TableCell>
                        <div class="flex items-center space-x-2">
                          <span :class="getStatusColor(field.status)">{{ field.qualityScore }}%</span>
                          <div class="w-16">
                            <Progress :value="field.qualityScore" class="h-2" />
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge :variant="field.issuesCount > 0 ? 'destructive' : 'secondary'">
                          {{ field.issuesCount }} issues
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div class="text-xs text-muted-foreground">
                          <div>Null: {{ field.nullPercentage }}%</div>
                          <div>Unique: {{ field.uniquePercentage }}%</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Button 
                          variant="outline" 
                          size="sm"
                          @click="onSelectField(field.id)"
                        >
                          Review
                        </Button>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="data" class="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Data Sample ({{ table.name }}) - Issues Highlighted</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead v-for="field in table.fields.slice(0, 6)" :key="field.id">
                        {{ field.name }}
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell>1</TableCell>
                      <TableCell>john.doe@example.com</TableCell>
                      <TableCell>+1-555-0123</TableCell>
                      <TableCell>32</TableCell>
                      <TableCell>active</TableCell>
                      <TableCell>2024-01-15</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>2</TableCell>
                      <TableCell class="bg-red-50">—</TableCell>
                      <TableCell class="bg-yellow-50">555.0124</TableCell>
                      <TableCell>28</TableCell>
                      <TableCell>active</TableCell>
                      <TableCell>2024-01-16</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>3</TableCell>
                      <TableCell>bob@example.com</TableCell>
                      <TableCell class="bg-yellow-50">(555) 012-5</TableCell>
                      <TableCell class="bg-blue-50">150</TableCell>
                      <TableCell>inactive</TableCell>
                      <TableCell>2024-01-17</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>4</TableCell>
                      <TableCell>alice@example.com</TableCell>
                      <TableCell class="bg-yellow-50">5550126</TableCell>
                      <TableCell>35</TableCell>
                      <TableCell>active</TableCell>
                      <TableCell>2024-01-18</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell class="bg-yellow-50">5</TableCell>
                      <TableCell>john2@example.com</TableCell>
                      <TableCell class="bg-yellow-50">+1 555 0127</TableCell>
                      <TableCell>32</TableCell>
                      <TableCell>active</TableCell>
                      <TableCell>2024-01-19</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
                <div class="mt-4 space-y-2">
                  <h4 class="font-medium">Issue Legend:</h4>
                  <div class="flex flex-wrap gap-4 text-sm">
                    <div class="flex items-center space-x-2">
                      <div class="w-4 h-4 bg-red-50 border border-red-200 rounded"></div>
                      <span>Missing values</span>
                    </div>
                    <div class="flex items-center space-x-2">
                      <div class="w-4 h-4 bg-yellow-50 border border-yellow-200 rounded"></div>
                      <span>Format issues / Duplicates</span>
                    </div>
                    <div class="flex items-center space-x-2">
                      <div class="w-4 h-4 bg-blue-50 border border-blue-200 rounded"></div>
                      <span>Outliers</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="issues" class="space-y-4">
            <!-- Table-wide Issues -->
            <Card v-if="tableWideIssues.length > 0">
              <CardHeader>
                <CardTitle>Table-wide Issues</CardTitle>
              </CardHeader>
              <CardContent>
                <div class="space-y-4">
                  <div 
                    v-for="issue in tableWideIssues" 
                    :key="issue.id" 
                    class="flex items-start space-x-4 p-4 border rounded-lg"
                  >
                    <div class="flex-shrink-0">
                      <component :is="getIssueIcon(issue.type)" />
                    </div>
                    <div class="flex-1">
                      <div class="flex items-center justify-between">
                        <h4 class="font-medium">{{ issue.description }}</h4>
                        <Badge :class="getSeverityColor(issue.severity)">
                          {{ issue.severity }}
                        </Badge>
                      </div>
                      <p class="text-sm text-muted-foreground mt-1">
                        {{ issue.affectedRows }} rows affected
                      </p>
                      <p class="text-sm mt-2">{{ issue.suggestion }}</p>
                      <div v-if="issue.businessImpact" class="mt-2 p-2 bg-blue-50 rounded text-sm">
                        <strong>Business Impact:</strong> {{ issue.businessImpact }}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <!-- Field-level Issues -->
            <Card v-if="fieldIssues.length > 0">
              <CardHeader>
                <CardTitle>Field-level Issues</CardTitle>
              </CardHeader>
              <CardContent>
                <div class="space-y-4">
                  <div 
                    v-for="issue in fieldIssues" 
                    :key="issue.id" 
                    class="flex items-start space-x-4 p-4 border rounded-lg"
                  >
                    <div class="flex-shrink-0">
                      <component :is="getIssueIcon(issue.type)" />
                    </div>
                    <div class="flex-1">
                      <div class="flex items-center justify-between">
                        <h4 class="font-medium">{{ issue.description }}</h4>
                        <Badge :class="getSeverityColor(issue.severity)">
                          {{ issue.severity }}
                        </Badge>
                      </div>
                      <p class="text-sm text-muted-foreground mt-1">
                        Field: <span class="font-mono">{{ getFieldById(issue.fieldId)?.name }}</span> • {{ issue.affectedRows }} rows affected
                      </p>
                      <p class="text-sm mt-2">{{ issue.suggestion }}</p>
                      <div v-if="issue.businessImpact" class="mt-2 p-2 bg-blue-50 rounded text-sm">
                        <strong>Business Impact:</strong> {{ issue.businessImpact }}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="metrics" class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Data Completeness</CardTitle>
                </CardHeader>
                <CardContent>
                  <div class="space-y-3">
                    <div 
                      v-for="field in table.fields.slice(0, 3)" 
                      :key="field.id" 
                      class="space-y-1"
                    >
                      <div class="flex justify-between text-sm">
                        <span class="font-mono">{{ field.name }}</span>
                        <span>{{ 100 - field.nullPercentage }}%</span>
                      </div>
                      <Progress :value="100 - field.nullPercentage" class="h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Data Uniqueness</CardTitle>
                </CardHeader>
                <CardContent>
                  <div class="space-y-3">
                    <div 
                      v-for="field in table.fields.slice(0, 3)" 
                      :key="field.id" 
                      class="space-y-1"
                    >
                      <div class="flex justify-between text-sm">
                        <span class="font-mono">{{ field.name }}</span>
                        <span>{{ field.uniquePercentage }}%</span>
                      </div>
                      <Progress :value="field.uniquePercentage" class="h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      <!-- AI Chat Sidebar -->
      <div class="space-y-4">
        <Card class="h-[600px] flex flex-col">
          <CardHeader>
            <CardTitle class="flex items-center space-x-2">
              <Bot class="w-5 h-5" />
              <span>Table Quality Agent</span>
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
                  <div :class="`max-w-[80%] rounded-lg p-3 ${
                    message.type === 'user' 
                      ? 'bg-primary text-primary-foreground' 
                      : 'bg-muted'
                  }`">
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
                  placeholder="Ask about table quality..."
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { 
  ArrowLeft, 
  Send, 
  Bot, 
  User,
  Table as TableIcon,
  FileX,
  Copy,
  AlertCircle,
  AlertTriangle,
  Key,
  Shield,
  Tag,
  BookOpen
} from 'lucide-vue-next'
import type { DataTable, QualityIssue, ChatMessage } from '@/types/data-quality'

interface Props {
  table: DataTable
  issues: QualityIssue[]
  onBack: () => void
  onSelectField: (fieldId: string) => void
}

const props = defineProps<Props>()

const getIssueIcon = (type: string) => {
  switch (type) {
    case 'missing_values':
      return FileX
    case 'duplicates':
      return Copy
    case 'inconsistent_format':
      return AlertTriangle
    case 'outliers':
      return AlertCircle
    case 'business_rule_violation':
      return Shield
    default:
      return AlertCircle
  }
}

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

const getStatusColor = (status: string) => {
  switch (status) {
    case 'good':
      return 'text-green-600'
    case 'warning':
      return 'text-yellow-600'
    case 'error':
      return 'text-red-600'
    default:
      return 'text-gray-600'
  }
}

const tableIssues = computed(() => props.issues.filter(issue => issue.tableId === props.table.id))
const fieldIssues = computed(() => tableIssues.value.filter(issue => issue.level === 'field'))
const tableWideIssues = computed(() => tableIssues.value.filter(issue => issue.level === 'table'))

const getFieldById = (fieldId?: string) => {
  return props.table.fields.find(f => f.id === fieldId)
}

const chatMessages = ref<ChatMessage[]>([
  {
    id: '1',
    type: 'agent',
    content: `I'm reviewing the "${props.table.name}" table. This table has a quality score of ${props.table.qualityScore}% with ${props.table.issuesCount} issues identified. The table contains ${props.table.recordCount.toLocaleString()} records. Would you like me to explain the main quality concerns?`,
    timestamp: '10:30 AM',
    context: {
      level: 'table',
      entityId: props.table.id,
      entityName: props.table.name
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
      level: 'table',
      entityId: props.table.id,
      entityName: props.table.name
    }
  }
  
  chatMessages.value.push(userMessage)
  newMessage.value = ''
  
  // Simulate AI response
  setTimeout(() => {
    const agentMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      type: 'agent',
      content: `Based on the semantic definition of "${props.table.name}" as "${props.table.businessDefinition}", I can help you understand how these quality issues might impact your business processes. Let me analyze the specific concerns you mentioned.`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      context: {
        level: 'table',
        entityId: props.table.id,
        entityName: props.table.name
      }
    }
    chatMessages.value.push(agentMessage)
  }, 1000)
}
</script>