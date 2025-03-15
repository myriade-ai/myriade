interface Column {
  name: string
  type: string
}

export interface Table {
  name: string
  schema: string
  description: string
  columns: Column[]
  used: boolean // information if the table is used in the query
}
