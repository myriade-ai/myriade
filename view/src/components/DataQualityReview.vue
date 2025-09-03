<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <Button variant="ghost" size="sm" @click="onBack">
          <ArrowLeft class="w-4 h-4 mr-2" />
          Back to Dashboard
        </Button>
        <div>
          <h1>{{ dataSource.name }}</h1>
          <p class="text-muted-foreground">
            {{ dataSource.type }} • {{ dataSource.recordCount.toLocaleString() }} records
          </p>
        </div>
      </div>
      <Badge
        :class="
          dataSource.qualityScore >= 90
            ? 'bg-green-100 text-green-800'
            : dataSource.qualityScore >= 70
              ? 'bg-yellow-100 text-yellow-800'
              : 'bg-red-100 text-red-800'
        "
      >
        Quality Score: {{ dataSource.qualityScore }}%
      </Badge>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Main Content -->
      <div class="lg:col-span-2 space-y-6">
        <Tabs default-value="tables" class="w-full">
          <TabsList class="grid w-full grid-cols-3">
            <TabsTrigger value="tables">Tables</TabsTrigger>
            <TabsTrigger value="issues">Quality Issues</TabsTrigger>
            <TabsTrigger value="metrics">Source Metrics</TabsTrigger>
          </TabsList>

          <TabsContent value="tables" class="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle class="flex items-center space-x-2">
                  <TableIcon class="w-5 h-5" />
                  <span>Tables in {{ dataSource.name }}</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div class="space-y-4">
                  <div
                    v-for="table in dataSource.tables"
                    :key="table.id"
                    class="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                    @click="onSelectTable?.(table.id)"
                  >
                    <div class="flex items-center space-x-4">
                      <TableIcon class="w-5 h-5 text-muted-foreground" />
                      <div>
                        <h4 class="font-medium">{{ table.name }}</h4>
                        <p class="text-sm text-muted-foreground">
                          {{ table.recordCount.toLocaleString() }} records •
                          {{ table.fields.length }} fields
                        </p>
                        <p
                          v-if="table.businessDefinition"
                          class="text-xs text-muted-foreground mt-1 max-w-md"
                        >
                          {{ table.businessDefinition }}
                        </p>
                        <div v-if="table.tags.length > 0" class="flex flex-wrap gap-1 mt-2">
                          <Badge
                            v-for="tag in table.tags.slice(0, 3)"
                            :key="tag"
                            variant="secondary"
                            class="text-xs"
                          >
                            <Tag class="w-2 h-2 mr-1" />
                            {{ tag }}
                          </Badge>
                          <Badge v-if="table.tags.length > 3" variant="secondary" class="text-xs">
                            +{{ table.tags.length - 3 }} more
                          </Badge>
                        </div>
                      </div>
                    </div>

                    <div class="flex items-center space-x-6">
                      <div class="text-right">
                        <div class="flex items-center space-x-2 mb-1">
                          <span class="text-sm">Quality:</span>
                          <Badge :class="getQualityBadgeColor(table.qualityScore)">
                            {{ table.qualityScore }}%
                          </Badge>
                        </div>
                        <div class="w-32">
                          <Progress :value="table.qualityScore" class="h-2" />
                        </div>
                      </div>

                      <div class="text-right">
                        <p class="text-sm font-medium">{{ table.issuesCount }} issues</p>
                        <p class="text-xs text-muted-foreground">Updated {{ table.lastUpdated }}</p>
                      </div>

                      <Button variant="outline" size="sm"> Review Table </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="issues" class="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Data Quality Issues</CardTitle>
              </CardHeader>
              <CardContent>
                <div class="space-y-4">
                  <!-- Show source-level issues only -->
                  <div class="p-4 bg-muted/50 rounded-lg">
                    <p class="text-sm text-muted-foreground">
                      Showing source-level quality issues. For detailed field-level issues, please
                      navigate to individual tables.
                    </p>
                  </div>

                  <!-- Summary of issues by table -->
                  <div
                    v-for="table in dataSource.tables"
                    :key="table.id"
                    class="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div class="flex items-center space-x-3">
                      <TableIcon class="w-4 h-4 text-muted-foreground" />
                      <div>
                        <h4 class="font-medium">{{ table.name }}</h4>
                        <p class="text-sm text-muted-foreground">
                          {{ table.issuesCount }} quality issues found
                        </p>
                      </div>
                    </div>
                    <div class="flex items-center space-x-3">
                      <Badge :class="getQualityBadgeColor(table.qualityScore)">
                        {{ table.qualityScore }}%
                      </Badge>
                      <Button variant="outline" size="sm" @click="onSelectTable?.(table.id)">
                        View Issues
                      </Button>
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
                  <CardTitle>Completeness</CardTitle>
                </CardHeader>
                <CardContent>
                  <div class="space-y-2">
                    <div class="flex justify-between">
                      <span class="text-sm">Overall</span>
                      <span class="text-sm">98.9%</span>
                    </div>
                    <Progress :value="98.9" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Uniqueness</CardTitle>
                </CardHeader>
                <CardContent>
                  <div class="space-y-2">
                    <div class="flex justify-between">
                      <span class="text-sm">Overall</span>
                      <span class="text-sm">99.3%</span>
                    </div>
                    <Progress :value="99.3" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Consistency</CardTitle>
                </CardHeader>
                <CardContent>
                  <div class="space-y-2">
                    <div class="flex justify-between">
                      <span class="text-sm">Overall</span>
                      <span class="text-sm">87.2%</span>
                    </div>
                    <Progress :value="87.2" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Validity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div class="space-y-2">
                    <div class="flex justify-between">
                      <span class="text-sm">Overall</span>
                      <span class="text-sm">99.8%</span>
                    </div>
                    <Progress :value="99.8" />
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
              <span>AI Data Quality Agent</span>
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
                  placeholder="Ask about data quality issues..."
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
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { ChatMessage, DataSource } from '@/types/data-quality'
import { ArrowLeft, Bot, Send, Table as TableIcon, Tag, User } from 'lucide-vue-next'
import { ref } from 'vue'

interface Props {
  dataSource: DataSource
  onBack: () => void
  onSelectTable?: (tableId: string) => void
}

const props = defineProps<Props>()

const getQualityBadgeColor = (score: number) => {
  if (score >= 90) return 'bg-green-100 text-green-800'
  if (score >= 70) return 'bg-yellow-100 text-yellow-800'
  return 'bg-red-100 text-red-800'
}

const chatMessages = ref<ChatMessage[]>([
  {
    id: '1',
    type: 'agent',
    content: `I'm reviewing the "${props.dataSource.name}" data source. This source has ${props.dataSource.tables.length} tables with an overall quality score of ${props.dataSource.qualityScore}%. There are ${props.dataSource.issuesCount} issues across all tables. Would you like me to explain the main quality concerns or dive into specific tables?`,
    timestamp: '10:30 AM',
    context: {
      level: 'source',
      entityId: props.dataSource.id,
      entityName: props.dataSource.name
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
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  chatMessages.value.push(userMessage)
  newMessage.value = ''

  // Simulate AI response
  setTimeout(() => {
    const agentMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      type: 'agent',
      content: `Based on the ${props.dataSource.name} source analysis, I can help you prioritize quality improvements across your ${props.dataSource.tables.length} tables. Would you like me to focus on the tables with the most critical issues or explain how these quality problems might impact your business processes?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      context: {
        level: 'source',
        entityId: props.dataSource.id,
        entityName: props.dataSource.name
      }
    }
    chatMessages.value.push(agentMessage)
  }, 1000)
}
</script>
