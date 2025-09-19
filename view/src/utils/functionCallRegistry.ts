import type { Component } from 'vue'
import type { FunctionCall } from '@/types/functionCalls'
import {
  isMemorySearchCall,
  isThinkCall,
  isAskUserCall,
  isSqlQueryCall,
  isSubmitCall
} from '@/types/functionCalls'

// Import renderer components
import MemorySearchRenderer from '@/components/functionCallRenderers/MemorySearchRenderer.vue'
import ThinkRenderer from '@/components/functionCallRenderers/ThinkRenderer.vue'
import AskUserRenderer from '@/components/functionCallRenderers/AskUserRenderer.vue'
import SqlQueryRenderer from '@/components/functionCallRenderers/SqlQueryRenderer.vue'
import SubmitRenderer from '@/components/functionCallRenderers/SubmitRenderer.vue'
import DefaultRenderer from '@/components/functionCallRenderers/DefaultRenderer.vue'

// Type for renderer entries
export interface RendererEntry {
  component: Component
  matcher: (functionCall: FunctionCall) => boolean
  priority: number // Higher priority = checked first
}

// Registry of all function call renderers
const rendererRegistry: RendererEntry[] = [
  {
    component: MemorySearchRenderer,
    matcher: isMemorySearchCall,
    priority: 100
  },
  {
    component: ThinkRenderer,
    matcher: isThinkCall,
    priority: 100
  },
  {
    component: AskUserRenderer,
    matcher: isAskUserCall,
    priority: 100
  },
  {
    component: SqlQueryRenderer,
    matcher: isSqlQueryCall,
    priority: 100
  },
  {
    component: SubmitRenderer,
    matcher: isSubmitCall,
    priority: 100
  },
  {
    component: DefaultRenderer,
    matcher: () => true, // Always matches (fallback)
    priority: 0
  }
]

/**
 * Get the appropriate renderer component for a function call
 */
export function getRendererForFunctionCall(functionCall: FunctionCall): Component {
  // Sort by priority (highest first) and find first match
  const sortedRegistry = rendererRegistry.sort((a, b) => b.priority - a.priority)

  for (const entry of sortedRegistry) {
    if (entry.matcher(functionCall)) {
      return entry.component
    }
  }

  // This should never happen due to fallback, but TypeScript safety
  return DefaultRenderer
}

/**
 * Register a new function call renderer
 * This allows for runtime extension of the system
 */
export function registerFunctionCallRenderer(entry: RendererEntry): void {
  rendererRegistry.unshift(entry) // Add at beginning for higher priority
}

/**
 * Get all registered renderers (for debugging/inspection)
 */
export function getAllRenderers(): readonly RendererEntry[] {
  return Object.freeze([...rendererRegistry])
}