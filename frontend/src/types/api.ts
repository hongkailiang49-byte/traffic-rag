export interface QueryRequest {
  question: string
  session_id?: string
  intent?: string
  filters?: Record<string, unknown>
  top_k?: number
}

export interface Source {
  content: string
  score: number
  source: string
}

export interface QueryResponse {
  answer: string
  intent: string
  sources: Source[]
  session_id: string
  phase: string
  clarification: string
}

export interface SessionRequest {
  session_id: string
  message: string
}

export interface SessionResponse {
  session_id: string
  phase: string
  response: string
  missing_slots: string[]
  collected_slots: Record<string, string>
}

export interface IngestRequest {
  directory?: string
}

export interface IngestResponse {
  total_files: number
  total_chunks: number
  success_files: number
  failed_files: string[]
  message: string
}

export interface HealthResponse {
  status: string
  components: Record<string, string>
}

export interface SessionOut {
  session_id: string
  intent: string
  created_at: string
  message_count: number
  first_message: string
}

export interface MessageOut {
  role: string
  content: string
  seq: number
  created_at: string
}
