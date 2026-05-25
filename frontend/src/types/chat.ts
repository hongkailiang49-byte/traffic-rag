import type { Source } from './api'

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  intent?: string
  sources?: Source[]
  timestamp: number
}
