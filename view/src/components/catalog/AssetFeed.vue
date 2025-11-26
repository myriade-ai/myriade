<template>
  <div class="space-y-4">
    <h3 class="text-sm font-medium text-muted-foreground">Activity</h3>

    <!-- Comment Input -->
    <div class="flex gap-3">
      <Avatar class="size-8 flex-shrink-0">
        <AvatarFallback class="bg-primary-100 text-primary-700 text-xs">
          {{ userInitials }}
        </AvatarFallback>
      </Avatar>
      <div class="flex-1 space-y-2">
        <Textarea
          v-model="commentText"
          placeholder="Leave a comment... Type @myriade-agent to ask AI"
          rows="2"
          class="resize-none text-sm"
          :disabled="isSubmitting"
          @keydown.meta.enter="submitComment"
          @keydown.ctrl.enter="submitComment"
        />
        <div class="flex justify-between items-center">
          <p class="text-xs text-muted-foreground">
            <span v-if="hasMentionAgent" class="text-primary-600">
              ✨ @myriade-agent will respond to your message
            </span>
            <span v-else> Press ⌘+Enter to send </span>
          </p>
          <Button
            size="sm"
            :disabled="!commentText.trim() || isSubmitting"
            :is-loading="isSubmitting"
            @click="submitComment"
          >
            <template #loading>Sending...</template>
            {{ hasMentionAgent ? 'Send to AI' : 'Comment' }}
          </Button>
        </div>
      </div>
    </div>

    <!-- Agent Conversation Sheet -->
    <AssetChatFeed v-model:open="showConversationSheet" :conversation-id="selectedConversationId" />

    <!-- Activity Timeline -->
    <div class="relative">
      <!-- Timeline line -->
      <div
        v-if="activities.length > 0"
        class="absolute left-4 top-0 bottom-0 w-px bg-border"
        aria-hidden="true"
      />

      <!-- Activities -->
      <div class="space-y-4">
        <div v-for="activity in activities" :key="activity.id" class="relative flex gap-3 pl-0">
          <!-- Avatar/Icon -->
          <div class="relative z-10 flex-shrink-0">
            <Avatar
              v-if="
                activity.activity_type === 'comment' || activity.activity_type === 'agent_message'
              "
              class="size-8 ring-4 ring-background"
            >
              <AvatarFallback
                :class="[
                  'text-xs',
                  activity.activity_type === 'agent_message'
                    ? 'bg-purple-100 text-purple-700'
                    : 'bg-primary-100 text-primary-700'
                ]"
              >
                {{
                  activity.activity_type === 'agent_message'
                    ? 'AI'
                    : getInitials(activity.actor_email)
                }}
              </AvatarFallback>
            </Avatar>
            <div
              v-else
              class="size-8 rounded-full bg-muted ring-4 ring-background flex items-center justify-center"
            >
              <component
                :is="getActivityIcon(activity.activity_type)"
                class="size-4 text-muted-foreground"
              />
            </div>
          </div>

          <!-- Content -->
          <div class="flex-1 min-w-0 pt-1">
            <!-- Comment or Agent Message -->
            <div
              v-if="
                activity.activity_type === 'comment' || activity.activity_type === 'agent_message'
              "
              class="space-y-1"
            >
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium">
                  {{
                    activity.activity_type === 'agent_message'
                      ? 'Myriade Agent'
                      : activity.actor_email
                  }}
                </span>
                <span class="text-xs text-muted-foreground">
                  {{ formatRelativeTime(activity.created_at) }}
                </span>
              </div>
              <MarkdownDisplay :content="activity.content ?? ''" />

              <!-- Link to conversation if agent was triggered -->
              <button
                v-if="activity.conversation_id"
                class="text-xs text-primary-600 hover:text-primary-700 hover:underline mt-1"
                @click="openConversation(activity.conversation_id)"
              >
                View conversation →
              </button>
            </div>

            <!-- Agent Working -->
            <button
              v-else-if="activity.activity_type === 'agent_working'"
              class="flex items-center gap-2 hover:bg-muted/50 rounded px-1 -mx-1 transition-colors cursor-pointer"
              @click="activity.conversation_id && openConversation(activity.conversation_id)"
            >
              <!-- Running status -->
              <template v-if="activity.status === 'running'">
                <span class="text-sm text-muted-foreground">
                  <span class="font-medium text-purple-600">Myriade Agent</span>
                  is analyzing...
                </span>
                <LoaderIcon class="size-3 text-purple-600" />
              </template>

              <!-- Finished status -->
              <template v-else-if="activity.status === 'finished'">
                <span class="text-sm text-muted-foreground">
                  <span class="font-medium text-purple-600">Myriade Agent</span>
                  completed analysis
                </span>
                <CheckCircleIcon class="size-3 text-green-600" />
              </template>

              <!-- Error status -->
              <template v-else-if="activity.status === 'error'">
                <span class="text-sm text-muted-foreground">
                  <span class="font-medium text-purple-600">Myriade Agent</span>
                  encountered an error
                </span>
                <AlertCircleIcon class="size-3 text-red-600" />
              </template>

              <!-- Fallback for unknown/null status (legacy) -->
              <template v-else>
                <span class="text-sm text-muted-foreground">
                  <span class="font-medium text-purple-600">Myriade Agent</span>
                  is analyzing...
                </span>
                <LoaderIcon class="size-3 text-purple-600" />
              </template>

              <span class="text-xs text-muted-foreground">
                {{ formatRelativeTime(activity.created_at) }}
              </span>
            </button>

            <!-- Audit Trail (description, tags, status updates) -->
            <div v-else class="space-y-1">
              <div class="flex items-center gap-2 text-sm">
                <span class="text-muted-foreground">
                  <span class="font-medium text-foreground">{{
                    activity.actor_email || 'System'
                  }}</span>
                  {{ getActivityVerb(activity.activity_type) }}
                </span>
                <span class="text-xs text-muted-foreground">
                  {{ formatRelativeTime(activity.created_at) }}
                </span>
              </div>

              <!-- Show changes for audit activities -->
              <div
                v-if="
                  activity.changes &&
                  (activity.changes.old !== undefined || activity.changes.new !== undefined)
                "
                class="text-xs mt-1 group/changes"
              >
                <div class="bg-muted/50 rounded px-2 py-1 space-y-0.5 relative">
                  <div
                    v-if="activity.changes.old"
                    :class="[
                      'text-red-600 line-through',
                      expandedActivities.has(activity.id) ? 'whitespace-pre-wrap' : 'truncate'
                    ]"
                  >
                    {{
                      formatChangeValue(activity.changes.old, expandedActivities.has(activity.id))
                    }}
                  </div>
                  <div
                    v-if="activity.changes.new"
                    :class="[
                      'text-green-600',
                      expandedActivities.has(activity.id) ? 'whitespace-pre-wrap' : 'truncate'
                    ]"
                  >
                    {{
                      formatChangeValue(activity.changes.new, expandedActivities.has(activity.id))
                    }}
                  </div>
                  <!-- Expand/Collapse button (visible on hover or when expanded) -->
                  <button
                    v-if="hasLongContent(activity.changes)"
                    :class="[
                      'absolute -bottom-2 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded-full',
                      'bg-muted border border-border text-muted-foreground',
                      'hover:bg-accent hover:text-accent-foreground transition-all',
                      'flex items-center gap-1 text-xs',
                      expandedActivities.has(activity.id)
                        ? 'opacity-100'
                        : 'opacity-0 group-hover/changes:opacity-100'
                    ]"
                    @click="toggleActivityExpanded(activity.id)"
                  >
                    <ChevronDownIcon
                      :class="[
                        'size-3 transition-transform',
                        expandedActivities.has(activity.id) ? 'rotate-180' : ''
                      ]"
                    />
                    {{ expandedActivities.has(activity.id) ? 'Collapse' : 'Expand' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div
        v-if="activities.length === 0 && !isLoading"
        class="text-center py-8 text-muted-foreground"
      >
        <MessageSquareIcon class="size-8 mx-auto mb-2 opacity-50" />
        <p class="text-sm">No activity yet</p>
        <p class="text-xs">Comments and changes will appear here</p>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-8">
        <LoaderIcon class="size-6 mx-auto text-muted-foreground" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useQuery, useQueryClient, useMutation } from '@tanstack/vue-query'
import axios from '@/plugins/axios'
import { socket } from '@/plugins/socket'
import { user } from '@/stores/auth'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import AssetChatFeed from '@/components/catalog/AssetChatFeed.vue'
import LoaderIcon from '@/components/icons/LoaderIcon.vue'
import {
  PencilIcon,
  TagIcon,
  CheckCircleIcon,
  SparklesIcon,
  XCircleIcon,
  MessageSquareIcon,
  AlertCircleIcon,
  ChevronDownIcon
} from 'lucide-vue-next'
import MarkdownDisplay from '../MarkdownDisplay.vue'

interface Props {
  assetId: string
}

const props = defineProps<Props>()

// Types
interface ActivityChange {
  old: unknown
  new: unknown
}

interface Activity {
  id: string
  asset_id: string
  actor_id: string | null
  actor_email: string | null
  activity_type: string
  content: string | null
  changes: Record<string, ActivityChange> | null
  conversation_id: string | null
  status: string | null // running, finished, error
  created_at: string
}

// State
const commentText = ref('')
const queryClient = useQueryClient()
const showConversationSheet = ref(false)
const selectedConversationId = ref<string | null>(null)
const expandedActivities = ref<Set<string>>(new Set())

// Computed
const userInitials = computed(() => {
  if (!user.value?.email) return '?'
  return getInitials(user.value.email)
})

const hasMentionAgent = computed(() => {
  return /@myriade-agent/i.test(commentText.value)
})

// Query for fetching activities
const { data: activitiesData, isLoading } = useQuery({
  queryKey: computed(() => ['asset-activities', props.assetId]),
  queryFn: async (): Promise<Activity[]> => {
    const response = await axios.get(`/api/catalogs/assets/${props.assetId}/activities`)
    return response.data
  },
  staleTime: 2 * 60 * 1000,
  gcTime: 5 * 60 * 1000,
  refetchOnWindowFocus: false
})

const activities = computed(() => activitiesData.value || [])

// Mutation for submitting comments
const { mutate: submitActivityMutation, isPending: isSubmitting } = useMutation({
  mutationFn: async (content: string) => {
    const response = await axios.post(`/api/catalogs/assets/${props.assetId}/activities`, {
      content
    })
    return response.data
  },
  onSuccess: (data) => {
    commentText.value = ''
    // Add the new activity to the cache
    queryClient.setQueryData<Activity[]>(['asset-activities', props.assetId], (old) => [
      data.activity,
      ...(old || [])
    ])

    // If agent was triggered, also add the agent_working activity
    if (data.agentTriggered && data.conversation) {
      // The agent_working activity should come from the socket event
    }
  }
})

// Helper functions
function getInitials(email: string | null | undefined): string {
  if (!email) return '?'
  const parts = email.split('@')[0].split(/[._-]/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return email.substring(0, 2).toUpperCase()
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function getActivityIcon(type: string) {
  switch (type) {
    case 'description_updated':
      return PencilIcon
    case 'tags_updated':
      return TagIcon
    case 'status_updated':
      return CheckCircleIcon
    case 'suggestion_accepted':
      return SparklesIcon
    case 'suggestion_rejected':
      return XCircleIcon
    default:
      return MessageSquareIcon
  }
}

function getActivityVerb(type: string): string {
  switch (type) {
    case 'description_updated':
      return 'updated the description'
    case 'tags_updated':
      return 'updated the tags'
    case 'status_updated':
      return 'changed the status'
    case 'suggestion_accepted':
      return 'accepted an AI suggestion'
    case 'suggestion_rejected':
      return 'rejected an AI suggestion'
    default:
      return 'made a change'
  }
}

const TRUNCATE_LENGTH = 100

function formatChangeValue(value: unknown, expanded = false): string {
  if (value === null || value === undefined) return '(empty)'
  if (Array.isArray(value)) {
    if (value.length === 0) return '(none)'
    // Handle array of objects with name property (e.g., tags)
    if (typeof value[0] === 'object' && value[0] !== null && 'name' in value[0]) {
      return value.map((v) => (v as { name: string }).name).join(', ')
    }
    return value.join(', ')
  }
  if (typeof value === 'string') {
    if (expanded) return value
    return value.length > TRUNCATE_LENGTH ? value.substring(0, TRUNCATE_LENGTH) + '...' : value
  }
  return String(value)
}

function hasLongContent(changes: Record<string, unknown> | null): boolean {
  if (!changes) return false
  const oldVal = changes.old
  const newVal = changes.new
  const isLong = (val: unknown) => typeof val === 'string' && val.length > TRUNCATE_LENGTH
  return isLong(oldVal) || isLong(newVal)
}

function toggleActivityExpanded(activityId: string) {
  if (expandedActivities.value.has(activityId)) {
    expandedActivities.value.delete(activityId)
  } else {
    expandedActivities.value.add(activityId)
  }
  // Trigger reactivity
  expandedActivities.value = new Set(expandedActivities.value)
}

function submitComment() {
  if (!commentText.value.trim() || isSubmitting.value) return
  submitActivityMutation(commentText.value.trim())
}

// Conversation Sheet functions
function openConversation(conversationId: string) {
  selectedConversationId.value = conversationId
  showConversationSheet.value = true
}

// Real-time updates via Socket.IO
function handleActivityCreated(data: { activity: Activity }) {
  if (data.activity.asset_id !== props.assetId) return

  queryClient.setQueryData<Activity[]>(['asset-activities', props.assetId], (old) => {
    if (!old) return [data.activity]
    // Avoid duplicates
    if (old.some((a) => a.id === data.activity.id)) return old
    return [data.activity, ...old]
  })
}

function handleActivityStatusUpdated(data: { activity_id: string; status: string }) {
  queryClient.setQueryData<Activity[]>(['asset-activities', props.assetId], (old) => {
    if (!old) return old
    return old.map((activity) =>
      activity.id === data.activity_id ? { ...activity, status: data.status } : activity
    )
  })
}

onMounted(() => {
  socket.on('catalog:activity:created', handleActivityCreated)
  socket.on('catalog:activity:status', handleActivityStatusUpdated)
})

onUnmounted(() => {
  socket.off('catalog:activity:created', handleActivityCreated)
  socket.off('catalog:activity:status', handleActivityStatusUpdated)
})
</script>
