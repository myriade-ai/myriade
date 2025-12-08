import { reactive } from 'vue'

/**
 * Global explorer state shared across all UnifiedExplorer instances.
 * This ensures that expanded/collapsed state persists when navigating between pages.
 */
const expandedNodes = reactive<Record<string, boolean>>({})

export function useExplorerState() {
  function isExpanded(key: string): boolean {
    return expandedNodes[key] ?? false
  }

  function expandNode(key: string) {
    expandedNodes[key] = true
  }

  function collapseNode(key: string) {
    expandedNodes[key] = false
  }

  function toggleNode(key: string) {
    expandedNodes[key] = !expandedNodes[key]
  }

  function setExpanded(key: string, value: boolean) {
    expandedNodes[key] = value
  }

  /**
   * Expand multiple nodes at once (useful for expanding all databases)
   */
  function expandNodes(keys: string[]) {
    keys.forEach((key) => {
      expandedNodes[key] = true
    })
  }

  /**
   * Check if a node has been explicitly set (vs using default)
   */
  function hasExplicitState(key: string): boolean {
    return key in expandedNodes
  }

  return {
    expandedNodes,
    isExpanded,
    expandNode,
    collapseNode,
    toggleNode,
    setExpanded,
    expandNodes,
    hasExplicitState
  }
}
