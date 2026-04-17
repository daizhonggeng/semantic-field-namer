export type User = {
  id: number
  username: string
  created_at: string
}

export type TokenResponse = {
  access_token: string
  token_type: string
  user: User
}

export type Project = {
  id: number
  name: string
  description?: string | null
  owner_id: number
  created_at: string
  updated_at: string
}

export type ProjectMember = {
  id: number
  username: string
  role: 'owner' | 'editor' | 'viewer'
  created_at: string
}

export type UserOption = {
  id: number
  username: string
}

export type AIHealth = {
  configured: boolean
  reachable: boolean
  model_checked: boolean
  fallback_needed: boolean
  base_url?: string | null
  source_name?: string | null
  provider_type?: string | null
  model: string
  checked_at?: string | null
  error?: string | null
}

export type AIConfigSource = {
  id: number
  name: string
  provider_type: 'openai_compatible'
  base_url: string
  model: string
  timeout_seconds: number
  max_retries: number
  is_active: boolean
  is_readonly: boolean
  api_key_masked: string
  created_at: string
  updated_at: string
}

export type StyleProfile = {
  project_id: number
  summary: string
  stats: Record<string, unknown>
  abbreviations: Record<string, string>
  model_summary_source: string
  matching_thresholds: {
    lexical_threshold: number
    semantic_score_threshold: number
    semantic_gap_threshold: number
  }
  updated_at?: string | null
}

export type StyleTask = {
  task_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  stage: string
  message: string
  progress: number
  result?: StyleProfile | null
  error?: string | null
}

export type GeneratedFieldResult = {
  comment_zh: string
  proposed_name: string
  source: string
  similarity_score?: number | null
  matched_reference?: Record<string, unknown> | null
  conflict_flags: string[]
  reason?: string | null
  is_new_term: boolean
}

export type ImportedField = {
  id: number
  table_name: string
  column_name: string
  column_comment_zh?: string | null
  canonical_comment_zh?: string | null
  data_type?: string | null
}

export type GenerateResponse = {
  run_id: number
  table_name: string
  ai_fallback_used: boolean
  results: GeneratedFieldResult[]
}

export type GenerationTask = {
  task_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  stage: string
  message: string
  progress: number
  result?: GenerateResponse | null
  error?: string | null
}

export type HistoryItem = {
  id: number
  table_name: string
  created_at: string
  summary: Record<string, unknown> & {
    total?: number
    ai_used?: boolean
    source_breakdown?: Record<string, number>
    generated_sql?: string
  }
}
