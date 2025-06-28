export interface Database {
  id: string
  createdAt: Date
  name: string
  engine: string
  details: any
  safe_mode: boolean
  dbt_catalog: any
  dbt_manifest: any
}

export const makeEmptyDatabase = () => ({
  id: '',
  createdAt: new Date(),
  name: '',
  engine: '',
  details: null,
  safe_mode: true,
  dbt_catalog: null,
  dbt_manifest: null
})

export const getDefaultDetailsForEngine = (engine: string) => {
  switch (engine) {
    case 'postgres':
      return { host: '', port: 5432, user: '', password: '', database: '' }
    case 'mysql':
      return { host: '', port: 3306, user: '', password: '', database: '' }
    case 'snowflake':
      return {
        account: '',
        user: '',
        password: '',
        database: '',
        schema: '',
        role: '',
        warehouse: ''
      }
    case 'sqlite':
      return { filename: '' }
    case 'bigquery':
      return { project_id: '', service_account_json: null }
    default:
      throw new Error('Unsupported engine')
  }
}

export const getDatabaseTypeName = (engine: string) => {
  const engineNames: Record<string, string> = {
    postgres: 'PostgreSQL',
    mysql: 'MySQL',
    snowflake: 'Snowflake',
    sqlite: 'SQLite',
    bigquery: 'BigQuery'
  }
  return engineNames[engine] || engine
}
