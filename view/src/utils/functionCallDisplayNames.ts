/**
 * Maps backend function call names to user-friendly display names
 */

export interface FunctionCallDisplayInfo {
  displayName: string
  description?: string
  icon?: string
  category?: string
}

// Mapping of function call patterns to display information
const functionCallDisplayMap: Record<string, FunctionCallDisplayInfo> = {
  // Database operations
  'DatabaseTool-database__sql_query': {
    displayName: 'SQL Query',
    description: 'Execute SQL query on database',
    icon: '🗄️',
    category: 'database'
  },
  sql_query: {
    displayName: 'SQL Query',
    description: 'Execute SQL query',
    icon: '🗄️',
    category: 'database'
  },

  // Memory operations
  memory_search: {
    displayName: 'Memory Search',
    description: 'Search through saved information',
    icon: '🔍',
    category: 'memory'
  },
  save_to_memory: {
    displayName: 'Save to Memory',
    description: 'Store information for later use',
    icon: '💾',
    category: 'memory'
  },

  // AI thinking and reasoning
  think: {
    displayName: 'Thinking',
    description: 'AI reasoning process',
    icon: '🤔',
    category: 'reasoning'
  },

  // User interaction
  ask_user: {
    displayName: 'Question',
    description: 'Ask user for clarification',
    icon: '❓',
    category: 'interaction'
  },

  // Chart and visualization
  'EchartsTool-echarts__preview_render': {
    displayName: 'Create Visualization',
    description: 'Generate chart from data',
    icon: '📊',
    category: 'visualization'
  },
  preview_render: {
    displayName: 'Create Chart',
    description: 'Generate data visualization',
    icon: '📊',
    category: 'visualization'
  },

  // Quality and catalog operations
  'SemanticCatalog-quality__create_entity': {
    displayName: 'Create Entity',
    description: 'Define new data entity',
    icon: '🏷️',
    category: 'catalog'
  },
  'SemanticCatalog-quality__update_entity': {
    displayName: 'Update Entity',
    description: 'Modify data entity definition',
    icon: '✏️',
    category: 'catalog'
  },
  'SemanticCatalog-quality__create_issue': {
    displayName: 'Report Issue',
    description: 'Create data quality issue',
    icon: '⚠️',
    category: 'quality'
  },

  // Catalog operations
  'CatalogTool-catalog__search_assets': {
    displayName: 'Search Assets',
    description: 'Find data assets in catalog',
    icon: '🔍',
    category: 'catalog'
  },
  'CatalogTool-catalog__get_asset_details': {
    displayName: 'Asset Details',
    description: 'Get detailed asset information',
    icon: '📋',
    category: 'catalog'
  }
}

// Pattern-based mappings for dynamic function names
const patternMappings: Array<{
  pattern: RegExp
  mapper: (match: RegExpMatchArray, originalName: string) => FunctionCallDisplayInfo
}> = [
  // Match any function ending with sql_query
  {
    pattern: /^.*sql_query$/,
    mapper: () => ({
      displayName: 'SQL Query',
      description: 'Execute database query',
      icon: '🗄️',
      category: 'database'
    })
  },

  // Match DatabaseTool operations
  {
    pattern: /^DatabaseTool-database__(.+)$/,
    mapper: (match) => ({
      displayName: formatFunctionName(match[1]),
      description: 'Database operation',
      icon: '🗄️',
      category: 'database'
    })
  },

  // Match EchartsTool operations
  {
    pattern: /^EchartsTool-echarts__(.+)$/,
    mapper: (match) => ({
      displayName: formatFunctionName(match[1]),
      description: 'Chart operation',
      icon: '📊',
      category: 'visualization'
    })
  },

  // Match SemanticCatalog operations
  {
    pattern: /^SemanticCatalog-quality__(.+)$/,
    mapper: (match) => ({
      displayName: formatFunctionName(match[1]),
      description: 'Data quality operation',
      icon: '🏷️',
      category: 'quality'
    })
  },

  // Match CatalogTool operations
  {
    pattern: /^CatalogTool-catalog__(.+)$/,
    mapper: (match) => ({
      displayName: formatFunctionName(match[1]),
      description: 'Catalog operation',
      icon: '📚',
      category: 'catalog'
    })
  },

  // Match WorkspaceTool operations
  {
    pattern: /^WorkspaceTool-workspace__(.+)$/,
    mapper: (match) => ({
      displayName: formatFunctionName(match[1]),
      description: 'Workspace operation',
      icon: '🏗️',
      category: 'workspace'
    })
  },

  // Match CodeEditor operations
  {
    pattern: /^CodeEditor-code_editor__read_file$/,
    mapper: () => ({
      displayName: 'Read File',
      description: 'View file contents',
      icon: '📄',
      category: 'code'
    })
  },
  {
    pattern: /^CodeEditor-code_editor__str_replace$/,
    mapper: () => ({
      displayName: 'Edit Code',
      description: 'Modify file content',
      icon: '✏️',
      category: 'code'
    })
  },
  {
    pattern: /^CodeEditor-code_editor__create_file$/,
    mapper: () => ({
      displayName: 'Create File',
      description: 'Create new file',
      icon: '📝',
      category: 'code'
    })
  }
]

/**
 * Convert snake_case or camelCase function names to Title Case
 */
function formatFunctionName(name: string): string {
  return name
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

/**
 * Get display information for a function call name
 */
export function getFunctionCallDisplayInfo(functionName: string): FunctionCallDisplayInfo {
  // First check exact matches
  const exactMatch = functionCallDisplayMap[functionName]
  if (exactMatch) {
    return exactMatch
  }

  // Then check pattern matches
  for (const { pattern, mapper } of patternMappings) {
    const match = functionName.match(pattern)
    if (match) {
      return mapper(match, functionName)
    }
  }

  // Fallback: format the raw name
  return {
    displayName: formatFunctionName(functionName),
    description: 'Function call',
    icon: '⚙️',
    category: 'general'
  }
}
