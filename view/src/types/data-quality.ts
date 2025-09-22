export interface DataSource {
  id: string
  name: string
  type: string
  qualityScore: number
  recordCount: number
  issuesCount: number
  lastUpdated: string
  status: 'good' | 'warning' | 'error'
  tables: DataTable[]
}

export interface DataTable {
  id: string
  name: string
  sourceId: string
  qualityScore: number
  recordCount: number
  issuesCount: number
  lastUpdated: string
  status: 'good' | 'warning' | 'error'
  businessDefinition?: string
  tags: string[]
  fields: DataField[]
}

export interface DataField {
  id: string
  name: string
  tableId: string
  dataType: string
  qualityScore: number
  issuesCount: number
  status: 'good' | 'warning' | 'error'
  businessDefinition?: string
  businessRules?: string[]
  tags: string[]
  isKey: boolean
  isSensitive: boolean
  nullPercentage: number
  uniquePercentage: number
}

export interface QualityIssue {
  id: string
  type:
    | 'missing_values'
    | 'duplicates'
    | 'inconsistent_format'
    | 'outliers'
    | 'invalid_data'
    | 'business_rule_violation'
  severity: 'high' | 'medium' | 'low'
  level: 'source' | 'table' | 'field'
  sourceId: string
  tableId?: string
  fieldId?: string
  description: string
  affectedRows: number
  suggestion: string
  businessImpact?: string
}

export interface SemanticRelationship {
  id: string
  type: 'foreign_key' | 'business_hierarchy' | 'derived_from' | 'aggregates_to'
  fromTableId: string
  fromFieldId?: string
  toTableId: string
  toFieldId?: string
  description: string
}

export interface BusinessGlossary {
  id: string
  term: string
  definition: string
  category: string
  relatedTerms: string[]
  examples?: string[]
}

export interface ChatMessage {
  id: string
  type: 'user' | 'agent'
  content: string
  timestamp: string
  context?: {
    level: 'source' | 'table' | 'field'
    entityId: string
    entityName: string
  }
}
