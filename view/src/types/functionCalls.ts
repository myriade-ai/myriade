// Base function call interface
export interface BaseFunctionCall {
  name: string
  arguments: Record<string, unknown>
}

// Specific function call interfaces
export interface MemorySearchCall extends BaseFunctionCall {
  name: 'memory_search'
  arguments: {
    search: string
  }
}

export interface ThinkCall extends BaseFunctionCall {
  name: 'think'
  arguments: {
    thought: string
  }
}

export interface AskUserCall extends BaseFunctionCall {
  name: 'ask_user'
  arguments: {
    question: string
  }
}

type SqlQueryFunctionName = 'sql_query' | `${string}sql_query`

export interface SqlQueryCall extends BaseFunctionCall {
  name: SqlQueryFunctionName
  arguments: {
    query: string
    title?: string
  }
}

export interface SubmitCall extends BaseFunctionCall {
  name: 'submit'
  arguments: Record<string, unknown>
}

export interface CodeEditorReadFileCall extends BaseFunctionCall {
  name: string // Pattern: CodeEditor-code_editor__read_file
  arguments: {
    path?: string
    content?: string
    [key: string]: unknown
  }
}

export interface CodeEditorReplaceCall extends BaseFunctionCall {
  name: string // Pattern: CodeEditor-code_editor__str_replace
  arguments: {
    path?: string
    old_string?: string
    new_string?: string
    [key: string]: unknown
  }
}

export interface CodeEditorCreateFileCall extends BaseFunctionCall {
  name: string // Pattern: CodeEditor-code_editor__create_file
  arguments: {
    path?: string
    content?: string
    [key: string]: unknown
  }
}

export type FunctionCall =
  | MemorySearchCall
  | ThinkCall
  | AskUserCall
  | SqlQueryCall
  | SubmitCall
  | CodeEditorReadFileCall
  | CodeEditorReplaceCall
  | CodeEditorCreateFileCall
  | BaseFunctionCall

// Props interface for renderer components
export interface FunctionCallRendererProps {
  functionCall: FunctionCall
  queryId?: string
  databaseSelectedId?: string | null
}

// Type guard functions for runtime type checking
export function isMemorySearchCall(call: FunctionCall): call is MemorySearchCall {
  return call.name === 'memory_search'
}

export function isThinkCall(call: FunctionCall): call is ThinkCall {
  return call.name === 'think'
}

export function isAskUserCall(call: FunctionCall): call is AskUserCall {
  return call.name === 'ask_user'
}

export function isSqlQueryCall(call: FunctionCall): call is SqlQueryCall {
  return call.name.endsWith('sql_query') || call.name === 'sql_query'
}

export function isSubmitCall(call: FunctionCall): call is SubmitCall {
  return call.name === 'submit'
}

export function isCodeEditorReadFileCall(call: FunctionCall): call is CodeEditorReadFileCall {
  return call.name.includes('code_editor__read_file')
}

export function isCodeEditorReplaceCall(call: FunctionCall): call is CodeEditorReplaceCall {
  return call.name.includes('code_editor__str_replace')
}

export function isCodeEditorCreateFileCall(call: FunctionCall): call is CodeEditorCreateFileCall {
  return call.name.includes('code_editor__create_file')
}
