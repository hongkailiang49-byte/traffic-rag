import { create } from 'zustand'
import { postLogin, postRegister, getMe } from '@/api/auth'
import type { UserInfo } from '@/types/auth'

interface AuthState {
  user: UserInfo | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean

  login: (email: string, password: string) => Promise<void>
  register: (email: string, name: string, password: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
  initFromStorage: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('rag_token'),
  isAuthenticated: !!localStorage.getItem('rag_token'),
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true })
    try {
      const res = await postLogin({ email, password })
      localStorage.setItem('rag_token', res.access_token)
      set({
        user: res.user,
        token: res.access_token,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (err: unknown) {
      set({ isLoading: false })
      throw err
    }
  },

  register: async (email: string, name: string, password: string) => {
    set({ isLoading: true })
    try {
      const res = await postRegister({ email, name, password })
      localStorage.setItem('rag_token', res.access_token)
      set({
        user: res.user,
        token: res.access_token,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (err: unknown) {
      set({ isLoading: false })
      throw err
    }
  },

  logout: () => {
    localStorage.removeItem('rag_token')
    set({ user: null, token: null, isAuthenticated: false })
  },

  fetchUser: async () => {
    try {
      const res = await getMe()
      set({ user: { email: res.email, name: res.name, clearance_level: res.clearance_level } })
    } catch {
      // Token 无效，清除
      localStorage.removeItem('rag_token')
      set({ user: null, token: null, isAuthenticated: false })
    }
  },

  initFromStorage: () => {
    const token = localStorage.getItem('rag_token')
    if (token) {
      set({ token, isAuthenticated: true })
    }
  },
}))
