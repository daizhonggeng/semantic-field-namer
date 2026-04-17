import axios from 'axios'

import type {
  AIConfigSource,
  AIHealth,
  GenerateResponse,
  GenerationTask,
  HistoryItem,
  ImportedField,
  Project,
  ProjectMember,
  StyleProfile,
  StyleTask,
  TokenResponse,
  User,
  UserOption,
} from '../types/api'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('semantic-field-namer-token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const authApi = {
  register: async (payload: { username: string; password: string }) =>
    (await api.post<TokenResponse>('/auth/register', payload)).data,
  login: async (payload: { username: string; password: string }) =>
    (await api.post<TokenResponse>('/auth/login', payload)).data,
  me: async () => (await api.get<User>('/auth/me')).data,
}

export const systemApi = {
  aiHealth: async () => (await api.get<AIHealth>('/system/ai-health')).data,
  listAiSources: async () => (await api.get<AIConfigSource[]>('/system/ai-sources')).data,
  createAiSource: async (payload: {
    name: string
    provider_type: 'openai_compatible'
    base_url: string
    api_key: string
    model: string
    timeout_seconds: number
    max_retries: number
    is_active: boolean
  }) => (await api.post<AIConfigSource>('/system/ai-sources', payload)).data,
  updateAiSource: async (
    sourceId: number,
    payload: {
      name: string
      provider_type: 'openai_compatible'
      base_url: string
      api_key?: string
      model: string
      timeout_seconds: number
      max_retries: number
      is_active: boolean
    },
  ) => (await api.put<AIConfigSource>(`/system/ai-sources/${sourceId}`, payload)).data,
  activateAiSource: async (sourceId: number) =>
    (await api.post<AIConfigSource>(`/system/ai-sources/${sourceId}/activate`)).data,
  deleteAiSource: async (sourceId: number) => (await api.delete(`/system/ai-sources/${sourceId}`)).data,
}

export const projectApi = {
  list: async () => (await api.get<Project[]>('/projects')).data,
  create: async (payload: { name: string; description?: string }) =>
    (await api.post<Project>('/projects', payload)).data,
  update: async (projectId: number, payload: { name: string; description?: string }) =>
    (await api.put<Project>(`/projects/${projectId}`, payload)).data,
  delete: async (projectId: number) => (await api.delete(`/projects/${projectId}`)).data,
  share: async (projectId: string, payload: { username: string; role: string }) =>
    (await api.post<ProjectMember>(`/projects/${projectId}/share`, payload)).data,
  members: async (projectId: string) =>
    (await api.get<ProjectMember[]>(`/projects/${projectId}/members`)).data,
  shareCandidates: async (projectId: string) =>
    (await api.get<UserOption[]>(`/projects/${projectId}/share-candidates`)).data,
  confirmMappings: async (
    projectId: string,
    payload: { items: Array<{ canonical_zh: string; english_name: string; alias_zh_list: string[] }> },
  ) => (await api.post(`/projects/${projectId}/mappings/confirm`, payload)).data,
}

export const importApi = {
  sql: async (projectId: string, payload: { source_name?: string; sql: string }) =>
    (await api.post(`/projects/${projectId}/imports/sql`, payload)).data,
  json: async (
    projectId: string,
    payload: { source_name?: string; fields: Array<Record<string, string | null>> },
  ) => (await api.post(`/projects/${projectId}/imports/json`, payload)).data,
  excel: async (projectId: string, payload: { source_name?: string; file: File }) => {
    const formData = new FormData()
    if (payload.source_name) {
      formData.append('source_name', payload.source_name)
    }
    formData.append('file', payload.file)
    return (
      await api.post(`/projects/${projectId}/imports/excel`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    ).data
  },
  txt: async (projectId: string, payload: { source_name?: string; content: string }) => {
    const formData = new FormData()
    if (payload.source_name) {
      formData.append('source_name', payload.source_name)
    }
    formData.append('content', payload.content)
    return (
      await api.post(`/projects/${projectId}/imports/txt`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    ).data
  },
  fields: async (projectId: string) =>
    (await api.get<ImportedField[]>(`/projects/${projectId}/imports/fields`)).data,
  updateField: async (
    projectId: string,
    fieldId: number,
    payload: { table_name: string; column_name: string; column_comment_zh?: string | null; data_type?: string | null },
  ) => (await api.put<ImportedField>(`/projects/${projectId}/imports/fields/${fieldId}`, payload)).data,
}

export const styleApi = {
  analyzeTask: async (projectId: string) =>
    (await api.post<{ task_id: string }>(`/projects/${projectId}/style/analyze-task`)).data,
  getAnalyzeTask: async (projectId: string, taskId: string) =>
    (await api.get<StyleTask>(`/projects/${projectId}/style/analysis-tasks/${taskId}`)).data,
  updateThresholds: async (
    projectId: string,
    payload: {
      lexical_threshold: number
      semantic_score_threshold: number
      semantic_gap_threshold: number
    },
  ) => (await api.put<StyleProfile>(`/projects/${projectId}/style/thresholds`, payload)).data,
  analyze: async (projectId: string) =>
    (await api.post<StyleProfile>(`/projects/${projectId}/style/analyze`)).data,
  profile: async (projectId: string) =>
    (await api.get<StyleProfile>(`/projects/${projectId}/style/profile`)).data,
}

export const generationApi = {
  createTask: async (
    projectId: string,
    payload: {
      table_name: string
      db_type: string
      existing_columns: string[]
      items: Array<{ comment_zh: string; data_type?: string; nullable: boolean; extra_context?: string }>
      preview_only: boolean
    },
  ) => (await api.post<{ task_id: string }>(`/projects/${projectId}/fields/generate-task`, payload)).data,
  getTask: async (projectId: string, taskId: string) =>
    (await api.get<GenerationTask>(`/projects/${projectId}/generation-tasks/${taskId}`)).data,
  generate: async (
    projectId: string,
    payload: {
      table_name: string
      db_type: string
      existing_columns: string[]
      items: Array<{ comment_zh: string; data_type?: string; nullable: boolean; extra_context?: string }>
      preview_only: boolean
    },
  ) => (await api.post<GenerateResponse>(`/projects/${projectId}/fields/generate`, payload)).data,
  history: async (projectId: string) =>
    (await api.get<HistoryItem[]>(`/projects/${projectId}/generation-runs`)).data,
}
