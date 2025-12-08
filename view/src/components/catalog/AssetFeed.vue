<template>
  <div class="space-y-2">
    <h3 class="text-xs font-medium uppercase tracking-wide text-foreground">Activity</h3>

    <!-- Comment Input Card -->
    <div class="rounded-lg border border-border bg-card overflow-hidden">
      <MarkdownEditor
        v-model="commentText"
        placeholder="Leave a comment... Type @ to mention Myriade Agent"
        :disabled="isSubmitting"
        :show-bubble-menu="false"
        :enable-agent-mention="true"
        :compact="true"
        min-height="50px"
        class="border-0"
        @submit="submitComment"
      />
      <div class="flex justify-between items-center px-3 py-2 border-t border-border bg-muted">
        <p class="text-[11px] text-muted-foreground">⌘+Enter to send</p>
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
          class="rounded-lg border border-border bg-card p-3"
        >
          <div class="flex gap-2.5">
            <Avatar class="size-7 flex-shrink-0">
              <AvatarFallback class="bg-muted text-muted-foreground text-[10px] font-medium">
                {{ getInitials(activity.actor_email) }}
              </AvatarFallback>
            </Avatar>
            <div class="flex-1 min-w-0">
              <div class="flex items-baseline gap-2 mb-0.5">
                <span class="text-[13px] font-medium text-foreground">
                  {{ getDisplayName(activity.actor_email) }}
                </span>
                <span class="text-[11px] text-muted-foreground">
                  {{ formatRelativeTime(activity.created_at) }}
                </span>
              </div>
              <div class="text-[13px] text-foreground leading-relaxed">
                <MarkdownDisplay :content="activity.content ?? ''" />
              </div>
            </div>
          </div>
        </div>

        <!-- Agent Message Card -->
        <div
          v-else-if="activity.activity_type === 'agent_message'"
          class="rounded-lg border border-gold/30 bg-gold/10 p-3"
        >
          <div class="flex gap-2.5">
            <div class="size-7 flex-shrink-0 rounded-full bg-gold flex items-center justify-center">
              <SparklesIcon class="size-3.5 text-black" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-baseline gap-2 mb-0.5">
                <span class="text-[13px] font-medium text-foreground">Myriade Agent</span>
                <span class="text-[11px] text-muted-foreground">
                  {{ formatRelativeTime(activity.created_at) }}
                </span>
              </div>
              <div class="text-[13px] text-foreground leading-relaxed">
                <MarkdownDisplay :content="activity.content ?? ''" />
              </div>
            </div>
          </div>
        </div>

        <!-- Agent Working Card -->
        <div
          v-else-if="activity.activity_type === 'agent_working'"
          class="rounded-lg border border-border bg-muted p-3"
        >
          <div class="flex gap-2.5">
            <div
              class="size-7 flex-shrink-0 rounded-full bg-card border border-border flex items-center justify-center"
            >
              <AlertCircleIcon
                v-if="activity.status === 'error'"
                class="size-3.5 text-destructive"
              />
              <CheckCircleIcon
                v-else-if="activity.status === 'finished'"
                class="size-3.5 text-green-600 dark:text-green-500"
              />
              <LoaderIcon v-else class="size-3.5 text-gold" />
            </div>
            <div class="flex-1 min-w-0 flex items-center justify-between">
              <div class="flex items-baseline gap-1.5">
                <span class="text-[13px] text-muted-foreground">
                  <span class="font-semibold text-foreground">Myriade Agent</span>
                  {{
                    activity.status === 'error'
                      ? 'encountered an error'
                      : activity.status === 'finished'
                        ? 'finished working'
                        : 'is working...'
                  }}
                </span>
                <span class="text-[10px] text-muted-foreground">
                  {{ formatRelativeTime(activity.created_at) }}
                </span>
              </div>
              <button
                v-if="activity.conversation_id"
                class="text-[11px] text-muted-foreground hover:text-foreground font-medium transition-colors"
                @click="openConversation(activity.conversation_id)"
              >
                View →
              </button>
            </div>
          </div>
        </div>

        <!-- Audit Trail (Compact) -->
        <div v-else class="rounded-lg border border-border bg-card p-3">
          <div class="flex items-start gap-2.5">
            <div
              class="size-7 rounded-full bg-muted flex items-center justify-center flex-shrink-0"
            >
              <component
                :is="getActivityIcon(activity.activity_type)"
                class="size-3.5 text-muted-foreground"
              />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-baseline gap-1.5 text-[13px] flex-wrap">
                <span class="font-medium text-foreground">
                  {{ getActorDisplayName(activity) }}
                </span>
                <span class="text-muted-foreground">
                  {{ getActivityVerb(activity.activity_type) }}
                </span>
                <span class="text-[11px] text-muted-foreground">
                  {{ formatRelativeTime(activity.created_at) }}
                </span>
              </div>

              <!-- Show changes for audit activities -->
              <div
                v-if="
                  activity.changes &&
                  (activity.changes.old !== undefined || activity.changes.new !== undefined)
                "
                class="mt-2"
              >
                <!-- Tags change display -->
                <div
                  v-if="activity.activity_type === 'tags_updated'"
                  class="flex flex-wrap items-center gap-1.5"
                >
                  <template v-if="getTagChanges(activity.changes).removed.length > 0">
                    <Badge
                      v-for="tag in getTagChanges(activity.changes).removed"
                      :key="`removed-${tag}`"
                      variant="secondary"
                      class="bg-red-500/10 text-red-700 dark:text-red-400 line-through"
                    >
                      {{ tag }}
                    </Badge>
                  </template>
                  <template v-if="getTagChanges(activity.changes).added.length > 0">
                    <Badge
                      v-for="tag in getTagChanges(activity.changes).added"
                      :key="`added-${tag}`"
                      variant="secondary"
                      class="bg-green-500/10 text-green-700 dark:text-green-400"
                    >
                      + {{ tag }}
                    </Badge>
                  </template>
                  <template v-if="getTagChanges(activity.changes).unchanged.length > 0">
                    <Badge
                      v-for="tag in getTagChanges(activity.changes).unchanged"
                      :key="`unchanged-${tag}`"
                      variant="secondary"
                      class="bg-gray-500/10 text-gray-700 dark:text-gray-400"
                    >
                      {{ tag }}
                    </Badge>
                  </template>
                </div>

                <!-- Status change display -->
                <div
                  v-else-if="activity.activity_type === 'status_updated'"
                  class="flex items-center gap-2"
                >
                  <AssetBadgeStatus
                    :status="activity.changes.old as unknown as AssetStatus"
                    badge-class="text-xs"
                  />
                  <ArrowRightIcon class="size-3 text-muted-foreground" />
                  <AssetBadgeStatus
                    :status="activity.changes.new as unknown as AssetStatus"
                    badge-class="text-xs"
                  />
                </div>

                <!-- Description/text change display - Unified Inline Diff -->
                <div v-else class="group/changes relative">
                  <div
                    :class="[
                      'rounded-md border border-border/60 overflow-hidden text-[12px] px-2.5 py-2',
                      expandedActivities.has(activity.id) ? '' : 'max-h-[52px]'
                    ]"
                  >
                    <p class="whitespace-pre-wrap break-words leading-relaxed">
                      <span
                        v-for="(part, index) in getUnifiedDiffParts(activity.changes)"
                        :key="index"
                        :class="[
                          part.type === 'added'
                            ? 'bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-300 rounded px-0.5'
                            : part.type === 'removed'
                              ? 'bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-300 line-through rounded px-0.5'
                              : 'text-foreground'
                        ]"
                        >{{ part.content }}</span
                      >
                    </p>
                    <!-- Empty state when both are empty -->
                    <div
                      v-if="getUnifiedDiffParts(activity.changes).length === 0"
                      class="text-muted-foreground italic text-center"
                    >
                      No changes
                    </div>
                  </div>
                  <!-- Expand/Collapse button -->
                  <button
                    v-if="hasLongContent(activity.changes)"
                    :class="[
                      'absolute -bottom-2.5 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded-full',
                      'bg-card border border-border text-muted-foreground shadow-sm',
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
      <div v-if="activities.length === 0 && !isLoading" class="text-center py-8">
        <MessageSquareIcon class="size-5 mx-auto text-muted-foreground/50 mb-2" />
        <p class="text-sm text-muted-foreground">No activity yet</p>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-10">
        <LoaderIcon class="size-4 mx-auto text-gold" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import AssetBadgeStatus from '@/components/AssetBadgeStatus.vue'
import MarkdownEditor from '@/components/MarkdownEditor.vue'
import AssetChatFeed from '@/components/catalog/AssetChatFeed.vue'
import LoaderIcon from '@/components/icons/LoaderIcon.vue'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import axios from '@/plugins/axios'
import { socket } from '@/plugins/socket'
import type { AssetStatus } from '@/stores/catalog'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import * as Diff from 'diff'
import {
  AlertCircleIcon,
  ArrowRightIcon,
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
  changes: ActivityChange | null
  conversation_id: string | null
  status: string | null // running, finished, error
  created_at: string
}

function getActorDisplayName(activity: Activity): string {
  if (activity.actor_id === 'myriade-agent') {
    return 'Myriade Agent'
  }
  return getDisplayName(activity.actor_email) || 'System'
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

function getTagChanges(changes: ActivityChange): {
  added: string[]
  removed: string[]
  unchanged: string[]
} {
  const extractTagNames = (val: unknown): string[] => {
    if (!val) return []
    if (Array.isArray(val)) {
      return val.map((v) => {
        if (typeof v === 'object' && v !== null && 'name' in v) {
          return (v as { name: string }).name
        }
        return String(v)
      })
    }
    return []
  }

  const oldTags = new Set(extractTagNames(changes.old))
  const newTags = new Set(extractTagNames(changes.new))

  const added = [...newTags].filter((t) => !oldTags.has(t))
  const removed = [...oldTags].filter((t) => !newTags.has(t))
  const unchanged = [...newTags].filter((t) => oldTags.has(t))

  return { added, removed, unchanged }
}

function hasLongContent(changes: ActivityChange | null): boolean {
  if (!changes) return false
  const oldVal = changes.old
  const newVal = changes.new
  const isLong = (val: unknown) => typeof val === 'string' && val.length > TRUNCATE_LENGTH
  return isLong(oldVal) || isLong(newVal)
}

interface DiffPart {
  type: 'added' | 'removed' | 'unchanged'
  content: string
}

function getUnifiedDiffParts(changes: ActivityChange | null): DiffPart[] {
  if (!changes) return []

  const oldText = typeof changes.old === 'string' ? changes.old : ''
  const newText = typeof changes.new === 'string' ? changes.new : ''

  // If both are empty, no diff to show
  if (!oldText && !newText) return []

  // Use word-level diff for a unified inline view
  const diffResult = Diff.diffWords(oldText, newText)
  const parts: DiffPart[] = []

  for (const part of diffResult) {
    if (part.added) {
      parts.push({ type: 'added', content: part.value })
    } else if (part.removed) {
      parts.push({ type: 'removed', content: part.value })
    } else {
      parts.push({ type: 'unchanged', content: part.value })
    }
  }

  return parts
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
