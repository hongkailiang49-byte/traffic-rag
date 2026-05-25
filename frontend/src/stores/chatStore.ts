import { create } from 'zustand'
import { v4 as uuid } from '@/lib/uuid'
import { postQuery } from '@/api/query'
import type { Message } from '@/types/chat'
import type { Source } from '@/types/api'

interface ChatState {
  messages: Message[]
  sessionId: string
  isLoading: boolean
  lastSources: Source[]
  sendMessage: (content: string, intent?: string) => Promise<void>
  clearMessages: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  sessionId: localStorage.getItem('rag_session_id') || uuid().slice(0, 8),
  isLoading: false,
  lastSources: [],

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
}))
