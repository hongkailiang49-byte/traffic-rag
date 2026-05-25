import { create } from 'zustand'
import { v4 as uuid } from '@/lib/uuid'
import { postSessionMessage } from '@/api/session'
import type { Message } from '@/types/chat'

type EmergencyPhase = 'collecting' | 'clarifying' | 'dispatched'

interface EmergencyState {
  phase: EmergencyPhase
  intent: string
  collectedSlots: Record<string, string>
  missingSlots: string[]
  dispatchOrder: string
  messages: Message[]
  sessionId: string
  isLoading: boolean
  sendMessage: (content: string) => Promise<void>
  reset: () => void
}

export const useEmergencyStore = create<EmergencyState>((set, get) => ({
  phase: 'collecting',
  intent: 'accident',
  collectedSlots: {},
  missingSlots: [],
  dispatchOrder: '',
  messages: [],
  sessionId: uuid().slice(0, 8),
  isLoading: false,

  sendMessage: async (content: string) => {
    const userMsg: Message = {
      id: uuid(),
      role: 'user',
      content,
      timestamp: Date.now(),
    }
    set((s) => ({ messages: [...s.messages, userMsg], isLoading: true }))

    try {
      const res = await postSessionMessage({
        session_id: get().sessionId,
        message: content,
      })

      const assistantMsg: Message = {
        id: uuid(),
        role: 'assistant',
        content: res.response,
        timestamp: Date.now(),
      }

      set((s) => ({
        messages: [...s.messages, assistantMsg],
        phase: res.phase as EmergencyPhase,
        collectedSlots: res.collected_slots,
        missingSlots: res.missing_slots,
        dispatchOrder: isDispatched ? res.response : '',
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

  reset: () => {
    const newId = uuid().slice(0, 8)
    set({
      phase: 'collecting',
      intent: 'accident',
      collectedSlots: {},
      missingSlots: [],
      dispatchOrder: '',
      messages: [],
      sessionId: newId,
      isLoading: false,
    })
  },
}))
