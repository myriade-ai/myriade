<template>
  <div class="border rounded-lg overflow-hidden bg-white">
    <!-- Header badge -->
    <button
      @click="isExpanded = !isExpanded"
      class="w-full flex items-center justify-between bg-gray-50 border-b px-3 py-2 hover:bg-gray-100 transition-colors cursor-pointer group"
    >
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">✏️ Code Edit</span>
        <span v-if="fileName" class="text-xs text-gray-500 font-mono">{{ fileName }}</span>
      </div>
      <div class="flex items-center gap-2">
        <span
          v-if="stats.added > 0"
          class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full"
        >
          +{{ stats.added }}
        </span>
        <span
          v-if="stats.removed > 0"
          class="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full"
        >
          -{{ stats.removed }}
        </span>
        <ChevronDownIcon
          :class="[
            'h-4 w-4 text-gray-500 transition-transform group-hover:text-gray-700',
            isExpanded && 'rotate-180'
          ]"
        />
      </div>
    </button>

    <!-- Expandable diff content -->
    <div v-if="isExpanded" class="max-h-96 overflow-y-auto">
      <div class="font-mono text-sm">
        <!-- Git-style diff display -->
        <div
          v-for="(hunk, hunkIndex) in diffHunks"
          :key="hunkIndex"
          class="border-b border-gray-200 last:border-b-0"
        >
          <!-- Hunk header -->
          <div class="bg-blue-50 border-l-4 border-blue-400 px-3 py-1 text-xs text-blue-800">
            {{ hunk.header }}
          </div>
          <!-- Diff lines -->
          <div
            v-for="(line, lineIndex) in hunk.lines"
            :key="lineIndex"
            :class="getDiffLineClasses(line)"
            class="flex"
          >
            <span class="w-12 text-xs text-gray-500 text-right pr-2 select-none flex-shrink-0">
              {{ line.oldLineNumber || '' }}
            </span>
            <span class="w-12 text-xs text-gray-500 text-right pr-2 select-none flex-shrink-0">
              {{ line.newLineNumber || '' }}
            </span>
            <span
              class="w-4 text-xs flex-shrink-0 select-none text-center"
              :class="getDiffPrefixClasses(line)"
            >
              {{ getDiffPrefix(line) }}
            </span>
            <span class="flex-1 px-2 whitespace-pre-wrap break-all">{{ line.content }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ChevronDownIcon } from '@heroicons/vue/24/outline'
import { diffLines, type Change } from 'diff'
import { computed, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    oldString?: string
    newString?: string
    fileName?: string
    defaultExpanded?: boolean
  }>(),
  {
    defaultExpanded: false
  }
)

const isExpanded = ref(props.defaultExpanded)

interface DiffLine {
  type: 'context' | 'added' | 'removed'
  content: string
  oldLineNumber?: number
  newLineNumber?: number
}

interface DiffHunk {
  header: string
  lines: DiffLine[]
}

// Generate git-style diff hunks
const diffHunks = computed((): DiffHunk[] => {
  if (!props.oldString && !props.newString) return []

  const oldText = props.oldString || ''
  const newText = props.newString || ''

  const changes = diffLines(oldText, newText)
  const hunks: DiffHunk[] = []

  let oldLineNumber = 1
  let newLineNumber = 1
  let currentHunk: DiffHunk | null = null

  changes.forEach((change: Change) => {
    const lines = change.value.split('\n').filter((line, index, array) => {
      // Remove the last empty line that results from splitting on \n
      return index < array.length - 1 || line !== ''
    })

    lines.forEach((line) => {
      if (!currentHunk) {
        currentHunk = {
          header: `@@ -${oldLineNumber},${getHunkSize(changes, true)} +${newLineNumber},${getHunkSize(changes, false)} @@`,
          lines: []
        }
      }

      const diffLine: DiffLine = {
        type: change.added ? 'added' : change.removed ? 'removed' : 'context',
        content: line,
        oldLineNumber: change.removed ? oldLineNumber : !change.added ? oldLineNumber : undefined,
        newLineNumber: change.added ? newLineNumber : !change.removed ? newLineNumber : undefined
      }

      currentHunk.lines.push(diffLine)

      if (!change.added) oldLineNumber++
      if (!change.removed) newLineNumber++
    })
  })

  if (currentHunk) {
    hunks.push(currentHunk)
  }

  return hunks
})

// Calculate hunk size for header
function getHunkSize(changes: Change[], isOld: boolean): number {
  return changes.reduce((total, change) => {
    if ((isOld && !change.added) || (!isOld && !change.removed)) {
      return total + change.value.split('\n').length - 1
    }
    return total
  }, 0)
}

// Get CSS classes for diff lines
function getDiffLineClasses(line: DiffLine): string {
  switch (line.type) {
    case 'added':
      return 'bg-green-50 hover:bg-green-100'
    case 'removed':
      return 'bg-red-50 hover:bg-red-100'
    case 'context':
      return 'hover:bg-gray-50'
    default:
      return ''
  }
}

// Get CSS classes for diff prefix
function getDiffPrefixClasses(line: DiffLine): string {
  switch (line.type) {
    case 'added':
      return 'text-green-700 font-bold'
    case 'removed':
      return 'text-red-700 font-bold'
    case 'context':
      return 'text-gray-400'
    default:
      return ''
  }
}

// Get diff prefix character
function getDiffPrefix(line: DiffLine): string {
  switch (line.type) {
    case 'added':
      return '+'
    case 'removed':
      return '-'
    case 'context':
      return ' '
    default:
      return ' '
  }
}

// Calculate statistics
const stats = computed(() => {
  const hunks = diffHunks.value
  let added = 0
  let removed = 0

  hunks.forEach((hunk) => {
    hunk.lines.forEach((line) => {
      if (line.type === 'added') added++
      if (line.type === 'removed') removed++
    })
  })

  return { added, removed }
})
</script>
