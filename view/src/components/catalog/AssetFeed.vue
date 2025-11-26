<template>
  <div class="space-y-4">
    <h3 class="text-xs font-medium text-muted-foreground uppercase tracking-wide">Activity</h3>

    <!-- Comment Input Card -->
    <div class="rounded-lg border border-border bg-card">
      <div class="p-1">
        <div class="flex gap-3">
          <div class="flex-1 min-w-0">
            <MarkdownEditor
              v-model="commentText"
              placeholder="Leave a comment... Type @ to mention AI"
              :disabled="isSubmitting"
              :show-bubble-menu="false"
              :enable-agent-mention="true"
              min-height="40px"
              @submit="submitComment"
            />
          </div>
        </div>
      </div>
      <div class="flex justify-between items-center px-3 py-2 border-t border-border bg-muted/20">
        <p class="text-[11px] text-muted-foreground">
          <span class="opacity-60">⌘+Enter to send</span>
        </p>
        <Button
          size="sm"
          variant="default"
          class="h-7 text-xs px-3"
          :disabled="!commentText.trim() || isSubmitting"
          :is-loading="isSubmitting"
          @click="submitComment"
        >
          <template #loading>Sending...</template>
          Comment
        </Button>
      </div>
    </div>

    <!-- Agent Conversation Sheet -->
    <AssetChatFeed v-model:open="showConversationSheet" :conversation-id="selectedConversationId" />

    <!-- Activity Feed -->
    <div class="space-y-2">
      <template v-for="activity in activities" :key="activity.id">
        <!-- Comment Card -->
        <div
          v-if="activity.activity_type === 'comment'"
          class="group rounded-lg border border-border bg-card hover:bg-muted/30 transition-colors"
        >
          <div class="p-3">
            <div class="flex gap-3">
              <Avatar class="size-7 flex-shrink-0">
                <AvatarFallback class="bg-muted text-muted-foreground text-[10px] font-medium">
                  {{ getInitials(activity.actor_email) }}
                </AvatarFallback>
              </Avatar>
              <div class="flex-1 min-w-0">
                <div class="flex items-baseline gap-2 mb-1">
                  <span class="text-sm font-medium text-foreground">
                    {{ getDisplayName(activity.actor_email) }}
                  </span>
                  <span class="text-[11px] text-muted-foreground">
                    {{ formatRelativeTime(activity.created_at) }}
                  </span>
                </div>
                <div class="text-sm text-foreground/80">
                  <MarkdownDisplay :content="activity.content ?? ''" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Agent Message Card -->
        <div
          v-else-if="activity.activity_type === 'agent_message'"
          class="group rounded-lg border border-border bg-card hover:bg-muted/30 transition-colors"
        >
          <div class="p-3">
            <div class="flex gap-3">
              <div
                class="size-7 flex-shrink-0 rounded-full bg-foreground flex items-center justify-center"
              >
                <SparklesIcon class="size-3.5 text-background" />
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-baseline gap-2 mb-1">
                  <span class="text-sm font-medium text-foreground"> Myriade Agent </span>
                  <span class="text-[11px] text-muted-foreground">
                    {{ formatRelativeTime(activity.created_at) }}
                  </span>
                </div>
                <div class="text-sm text-foreground/80">
                  <MarkdownDisplay :content="activity.content ?? ''" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Agent Working Card -->
        <div
          v-else-if="activity.activity_type === 'agent_working'"
          class="rounded-lg border border-border bg-muted/20"
        >
          <div class="px-3 py-2.5 flex items-center justify-between">
            <div class="flex items-center gap-2.5">
              <div class="size-5 rounded-full bg-muted flex items-center justify-center">
                <AlertCircleIcon
                  v-if="activity.status === 'error'"
                  class="size-3 text-muted-foreground"
                />
                <CheckCircleIcon
                  v-else-if="activity.status === 'finished'"
                  class="size-3 text-muted-foreground"
                />
                <LoaderIcon v-else class="size-3 text-muted-foreground" />
              </div>
              <div class="flex items-baseline gap-1.5">
                <span class="text-sm text-muted-foreground">
                  <span class="font-medium text-foreground">AI</span>
                  {{
                    activity.status === 'error'
                      ? 'encountered an error'
                      : activity.status === 'finished'
                        ? 'finished working'
                        : 'is working...'
                  }}
                </span>
                <span class="text-[11px] text-muted-foreground/60">
                  {{ formatRelativeTime(activity.created_at) }}
                </span>
              </div>
            </div>
            <button
              v-if="activity.conversation_id"
              class="text-[11px] text-muted-foreground hover:text-foreground font-medium transition-colors"
              @click="openConversation(activity.conversation_id)"
            >
              View in conversation →
            </button>
          </div>
        </div>

        <!-- Audit Trail (Compact) -->
        <div v-else class="px-1">
          <div class="flex items-start gap-2.5 py-1.5">
            <div
              class="size-5 rounded-full bg-muted flex items-center justify-center flex-shrink-0 mt-0.5"
            >
              <component
                :is="getActivityIcon(activity.activity_type)"
                class="size-3 text-muted-foreground"
              />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-baseline gap-1.5 text-[13px]">
                <span class="font-medium text-foreground/80">
                  {{ getDisplayName(activity.actor_email) || 'System' }}
                </span>
                <span class="text-muted-foreground">
                  {{ getActivityVerb(activity.activity_type) }}
                </span>
                <span class="text-[11px] text-muted-foreground/50">
                  {{ formatRelativeTime(activity.created_at) }}
                </span>
              </div>

              <!-- Show changes for audit activities -->
              <div
                v-if="
                  activity.changes &&
                  (activity.changes.old !== undefined || activity.changes.new !== undefined)
                "
                class="mt-1.5 group/changes"
              >
                <div
                  class="text-xs bg-muted/40 rounded-md px-2.5 py-1.5 space-y-0.5 border border-border/50 relative"
                >
                  <div
                    v-if="activity.changes.old"
                    :class="[
                      'text-muted-foreground line-through',
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
                      'text-foreground',
                      expandedActivities.has(activity.id) ? 'whitespace-pre-wrap' : 'truncate'
                    ]"
                  >
                    {{
                      formatChangeValue(activity.changes.new, expandedActivities.has(activity.id))
                    }}
                  </div>
                  <!-- Expand/Collapse button -->
                  <button
                    v-if="hasLongContent(activity.changes)"
                    :class="[
                      'absolute -bottom-2.5 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded-full',
                      'bg-background border border-border text-muted-foreground',
                      'hover:bg-muted hover:text-foreground transition-all',
                      'flex items-center gap-0.5 text-[10px] font-medium',
                      expandedActivities.has(activity.id)
                        ? 'opacity-100'
                        : 'opacity-0 group-hover/changes:opacity-100'
                    ]"
                    @click="toggleActivityExpanded(activity.id)"
                  >
                    <ChevronDownIcon
                      :class="[
                        'size-2.5 transition-transform',
                        expandedActivities.has(activity.id) ? 'rotate-180' : ''
                      ]"
                    />
                    {{ expandedActivities.has(activity.id) ? 'Less' : 'More' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Empty State -->
      <div
        v-if="activities.length === 0 && !isLoading"
        class="text-center py-12 text-muted-foreground"
      >
        <div class="size-10 mx-auto mb-3 rounded-full bg-muted flex items-center justify-center">
          <MessageSquareIcon class="size-4" />
        </div>
        <p class="text-sm font-medium">No activity yet</p>
        <p class="text-xs opacity-60 mt-0.5">Comments and changes will appear here</p>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-12">
        <LoaderIcon class="size-5 mx-auto text-muted-foreground" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import MarkdownEditor from '@/components/MarkdownEditor.vue'
import AssetChatFeed from '@/components/catalog/AssetChatFeed.vue'
import LoaderIcon from '@/components/icons/LoaderIcon.vue'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import axios from '@/plugins/axios'
import { socket } from '@/plugins/socket'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import {
  AlertCircleIcon,
  CheckCircleIcon,
  ChevronDownIcon,
  MessageSquareIcon,
  PencilIcon,
  SparklesIcon,
  TagIcon,
  XCircleIcon
} from 'lucide-vue-next'
import { computed, onMounted, onUnmounted, ref } from 'vue'
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
    queryClient.setQueryData<Activity[]>(['asset-activities', props.assetId], (old) => {
      if (!old) return [data.activity]
      // Avoid duplicates
      if (old.some((a) => a.id === data.activity.id)) return old
      return [data.activity, ...old]
    })

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

function getDisplayName(email: string | null | undefined): string {
  if (!email) return ''
  const username = email.split('@')[0]
  // Convert snake_case or kebab-case to Title Case
  return username
    .split(/[._-]/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(' ')
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
