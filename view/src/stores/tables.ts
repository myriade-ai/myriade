interface Column {
  id: string
  name: string
  type: string
  description: string
}

export interface Table {
  name: string
  schema: string
  databaseName?: string | null // database name for fully qualified table references
  description: string
  columns: Column[]
  used: boolean // information if the table is used in the query
}
