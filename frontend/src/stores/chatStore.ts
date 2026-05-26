import { create } from 'zustand'
import { v4 as uuid } from '@/lib/uuid'
import { postQuery } from '@/api/query'
import { getSessions, getSessionMessages, deleteSession as apiDeleteSession } from '@/api/session'
import type { Message } from '@/types/chat'
import type { Source, SessionOut } from '@/types/api'

interface ChatState {
  messages: Message[]
  sessionId: string
  isLoading: boolean
  lastSources: Source[]
  sessions: SessionOut[]
  sendMessage: (content: string, intent?: string) => Promise<void>
  clearMessages: () => void
  loadSessions: () => Promise<void>
  loadSession: (sessionId: string) => Promise<void>
  deleteSession: (sessionId: string) => Promise<void>
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  sessionId: localStorage.getItem('rag_session_id') || uuid().slice(0, 8),
  isLoading: false,
  lastSources: [],
  sessions: [],

  sendMessage: async (content: string, intent = 'auto') => {
    const userMsg: Message = {
      id: uuid(),
      role: 'user',
      content,
      timestamp: Date.now(),
    }
    set((s) => ({ messages: [...s.messages, userMsg], isLoading: true }))

    try {
      const res = await postQuery({
        question: content,
        session_id: get().sessionId,
        intent,
        top_k: 5,
      })
      localStorage.setItem('rag_session_id', res.session_id)

      const assistantMsg: Message = {
        id: uuid(),
        role: 'assistant',
        content: res.answer,
        intent: res.intent,
        sources: res.sources,
        timestamp: Date.now(),
      }
      set((s) => ({
        messages: [...s.messages, assistantMsg],
        sessionId: res.session_id,
        lastSources: res.sources,
        isLoading: false,
      }))
      // refresh session list in background
      get().loadSessions()
    } catch (err: unknown) {
      const errorMsg: Message = {
        id: uuid(),
        role: 'system',
        content: `请求失败：${err instanceof Error ? err.message : '未知错误'}`,
        timestamp: Date.now(),
      }
      set((s) => ({ messages: [...s.messages, errorMsg], isLoading: false }))
    }
  },

  clearMessages: () => {
    const newId = uuid().slice(0, 8)
    localStorage.setItem('rag_session_id', newId)
    set({ messages: [], sessionId: newId, lastSources: [] })
  },

  loadSessions: async () => {
    try {
      const sessions = await getSessions()
      set({ sessions })
    } catch {
      // silently fail
    }
  },

  loadSession: async (sessionId: string) => {
    set({ isLoading: true })
    try {
      const raw = await getSessionMessages(sessionId)
      const messages: Message[] = raw.map((m) => ({
        id: uuid(),
        role: m.role as Message['role'],
        content: m.content,
        timestamp: new Date(m.created_at).getTime(),
      }))
      localStorage.setItem('rag_session_id', sessionId)
      set({ messages, sessionId, lastSources: [], isLoading: false })
    } catch {
      set({ isLoading: false })
    }
  },

  deleteSession: async (sessionId: string) => {
    try {
      await apiDeleteSession(sessionId)
      set((s) => {
        const sessions = s.sessions.filter((x) => x.session_id !== sessionId)
        if (s.sessionId === sessionId) {
          const newId = uuid().slice(0, 8)
          localStorage.setItem('rag_session_id', newId)
          return { sessions, messages: [], sessionId: newId, lastSources: [] }
        }
        return { sessions }
      })
    } catch {
      // silently fail
    }
  },
}))
