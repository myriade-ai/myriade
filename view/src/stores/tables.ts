interface Column {
  name: string
  type: string
}

export interface Table {
  name: string
  schema: string
  description: string
  columns: Column[]
  used: Boolean // information if the table is used in the query
}
