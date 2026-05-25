import { create } from 'zustand'

interface ThemeState {
  theme: 'light' | 'dark'
  toggle: () => void
}

const saved = localStorage.getItem('rag_theme') as 'light' | 'dark' | null
const initial = saved || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')

if (initial === 'dark') document.documentElement.classList.add('dark')

export const useThemeStore = create<ThemeState>((set) => ({
  theme: initial,
  toggle: () =>
    set((state) => {
      const next = state.theme === 'light' ? 'dark' : 'light'
      localStorage.setItem('rag_theme', next)
      document.documentElement.classList.toggle('dark', next === 'dark')
      return { theme: next }
    }),
}))
