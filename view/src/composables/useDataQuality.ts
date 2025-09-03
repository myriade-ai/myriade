import { computed, ref } from 'vue'

export interface DataQualityMetrics {
  completeness: number
  accuracy: number
  consistency: number
  validity: number
  uniqueness: number
}

export interface ColumnProfile {
  name: string
  type: string
  nullCount: number
  uniqueCount: number
  totalCount: number
  invalidCount: number
  duplicateCount: number
}

export interface DataQualityIssue {
  id: string
  column: string
  type: 'missing' | 'invalid' | 'duplicate' | 'inconsistent'
  severity: 'low' | 'medium' | 'high'
  message: string
  count: number
  percentage: number
}

export function useDataQuality() {
  const isAnalyzing = ref(false)
  const analysisResults = ref<DataQualityMetrics | null>(null)
  const columnProfiles = ref<ColumnProfile[]>([])
  const issues = ref<DataQualityIssue[]>([])

  /**
   * Analyze data quality for a given dataset
   */
  const analyzeDataQuality = async (data: any[], columns: string[]) => {
    isAnalyzing.value = true
    
    try {
      // Simulate analysis delay
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const profiles = analyzeColumns(data, columns)
      const metrics = calculateOverallMetrics(profiles)
      const detectedIssues = detectIssues(profiles)
      
      columnProfiles.value = profiles
      analysisResults.value = metrics
      issues.value = detectedIssues
      
      return {
        metrics,
        profiles,
        issues: detectedIssues
      }
    } finally {
      isAnalyzing.value = false
    }
  }

  /**
   * Analyze individual columns
   */
  const analyzeColumns = (data: any[], columns: string[]): ColumnProfile[] => {
    return columns.map(column => {
      const values = data.map(row => row[column])
      const totalCount = values.length
      const nullCount = values.filter(v => v == null || v === '').length
      const nonNullValues = values.filter(v => v != null && v !== '')
      const uniqueValues = new Set(nonNullValues)
      const uniqueCount = uniqueValues.size
      
      // Detect data type
      const type = detectDataType(nonNullValues)
      
      // Count invalid values based on type
      const invalidCount = countInvalidValues(nonNullValues, type)
      
      // Count duplicates
      const duplicateCount = nonNullValues.length - uniqueCount
      
      return {
        name: column,
        type,
        nullCount,
        uniqueCount,
        totalCount,
        invalidCount,
        duplicateCount
      }
    })
  }

  /**
   * Detect data type of a column
   */
  const detectDataType = (values: any[]): string => {
    if (values.length === 0) return 'UNKNOWN'
    
    const sample = values.slice(0, 100) // Sample first 100 values
    
    // Check for numbers
    const numericCount = sample.filter(v => !isNaN(Number(v))).length
    if (numericCount > sample.length * 0.8) {
      const integerCount = sample.filter(v => Number.isInteger(Number(v))).length
      return integerCount > sample.length * 0.8 ? 'INTEGER' : 'DECIMAL'
    }
    
    // Check for dates
    const dateCount = sample.filter(v => !isNaN(Date.parse(v))).length
    if (dateCount > sample.length * 0.8) return 'DATE'
    
    // Check for booleans
    const boolCount = sample.filter(v => 
      typeof v === 'boolean' || ['true', 'false', '1', '0'].includes(String(v).toLowerCase())
    ).length
    if (boolCount > sample.length * 0.8) return 'BOOLEAN'
    
    // Check for emails
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    const emailCount = sample.filter(v => emailRegex.test(String(v))).length
    if (emailCount > sample.length * 0.8) return 'EMAIL'
    
    return 'VARCHAR'
  }

  /**
   * Count invalid values based on data type
   */
  const countInvalidValues = (values: any[], type: string): number => {
    switch (type) {
      case 'EMAIL':
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        return values.filter(v => !emailRegex.test(String(v))).length
      
      case 'INTEGER':
        return values.filter(v => !Number.isInteger(Number(v))).length
      
      case 'DECIMAL':
        return values.filter(v => isNaN(Number(v))).length
      
      case 'DATE':
        return values.filter(v => isNaN(Date.parse(v))).length
      
      case 'BOOLEAN':
        return values.filter(v => 
          typeof v !== 'boolean' && !['true', 'false', '1', '0'].includes(String(v).toLowerCase())
        ).length
      
      default:
        return 0
    }
  }

  /**
   * Calculate overall quality metrics
   */
  const calculateOverallMetrics = (profiles: ColumnProfile[]): DataQualityMetrics => {
    const totalCells = profiles.reduce((sum, p) => sum + p.totalCount, 0)
    const totalNulls = profiles.reduce((sum, p) => sum + p.nullCount, 0)
    const totalInvalid = profiles.reduce((sum, p) => sum + p.invalidCount, 0)
    const totalDuplicates = profiles.reduce((sum, p) => sum + p.duplicateCount, 0)
    
    const completeness = ((totalCells - totalNulls) / totalCells) * 100
    const validity = ((totalCells - totalInvalid) / totalCells) * 100
    const uniqueness = ((totalCells - totalDuplicates) / totalCells) * 100
    
    // Placeholder calculations for accuracy and consistency
    const accuracy = Math.min(validity, completeness)
    const consistency = (validity + uniqueness) / 2
    
    return {
      completeness: Math.round(completeness),
      accuracy: Math.round(accuracy),
      consistency: Math.round(consistency),
      validity: Math.round(validity),
      uniqueness: Math.round(uniqueness)
    }
  }

  /**
   * Detect data quality issues
   */
  const detectIssues = (profiles: ColumnProfile[]): DataQualityIssue[] => {
    const issues: DataQualityIssue[] = []
    
    profiles.forEach(profile => {
      // Missing values
      if (profile.nullCount > 0) {
        const percentage = (profile.nullCount / profile.totalCount) * 100
        issues.push({
          id: `missing-${profile.name}`,
          column: profile.name,
          type: 'missing',
          severity: percentage > 20 ? 'high' : percentage > 10 ? 'medium' : 'low',
          message: `${profile.nullCount} missing values (${percentage.toFixed(1)}%)`,
          count: profile.nullCount,
          percentage
        })
      }
      
      // Invalid values
      if (profile.invalidCount > 0) {
        const percentage = (profile.invalidCount / profile.totalCount) * 100
        issues.push({
          id: `invalid-${profile.name}`,
          column: profile.name,
          type: 'invalid',
          severity: percentage > 10 ? 'high' : percentage > 5 ? 'medium' : 'low',
          message: `${profile.invalidCount} invalid ${profile.type} values (${percentage.toFixed(1)}%)`,
          count: profile.invalidCount,
          percentage
        })
      }
      
      // Duplicate values (for columns that should be unique)
      if (profile.duplicateCount > profile.totalCount * 0.1) {
        const percentage = (profile.duplicateCount / profile.totalCount) * 100
        issues.push({
          id: `duplicate-${profile.name}`,
          column: profile.name,
          type: 'duplicate',
          severity: percentage > 30 ? 'high' : percentage > 15 ? 'medium' : 'low',
          message: `${profile.duplicateCount} duplicate values (${percentage.toFixed(1)}%)`,
          count: profile.duplicateCount,
          percentage
        })
      }
    })
    
    return issues.sort((a, b) => {
      const severityOrder = { high: 3, medium: 2, low: 1 }
      return severityOrder[b.severity] - severityOrder[a.severity]
    })
  }

  /**
   * Generate data quality report
   */
  const generateReport = () => {
    if (!analysisResults.value) return null
    
    const overallScore = Object.values(analysisResults.value).reduce((sum, score) => sum + score, 0) / 5
    
    return {
      overallScore: Math.round(overallScore),
      metrics: analysisResults.value,
      columnCount: columnProfiles.value.length,
      totalIssues: issues.value.length,
      highSeverityIssues: issues.value.filter(i => i.severity === 'high').length,
      recommendations: generateRecommendations()
    }
  }

  /**
   * Generate recommendations based on analysis
   */
  const generateRecommendations = (): string[] => {
    const recommendations: string[] = []
    
    const highIssues = issues.value.filter(i => i.severity === 'high')
    
    if (highIssues.some(i => i.type === 'missing')) {
      recommendations.push('Address missing values in critical columns')
    }
    
    if (highIssues.some(i => i.type === 'invalid')) {
      recommendations.push('Implement data validation rules for invalid formats')
    }
    
    if (highIssues.some(i => i.type === 'duplicate')) {
      recommendations.push('Set up deduplication processes for key columns')
    }
    
    if (recommendations.length === 0) {
      recommendations.push('Data quality looks good! Consider regular monitoring.')
    }
    
    return recommendations
  }

  const overallQualityScore = computed(() => {
    if (!analysisResults.value) return 0
    return Math.round(
      Object.values(analysisResults.value).reduce((sum, score) => sum + score, 0) / 5
    )
  })

  return {
    isAnalyzing,
    analysisResults,
    columnProfiles,
    issues,
    overallQualityScore,
    analyzeDataQuality,
    generateReport
  }
}