import { create } from 'zustand'
import { getHealth } from '@/api/health'

interface HealthState {
  status: 'ok' | 'degraded' | 'down'
  components: Record<string, string>
  lastChecked: number | null
  fetchHealth: () => Promise<void>
}

export const useHealthStore = create<HealthState>((set) => ({
  status: 'down',
  components: {},
  lastChecked: null,
  fetchHealth: async () => {
    try {
      const res = await getHealth()
      const allReady = Object.values(res.components).every((v) => v === 'ready')
      set({
        status: res.status === 'ok' && allReady ? 'ok' : 'degraded',
        components: res.components,
        lastChecked: Date.now(),
      })
    } catch {
      set({ status: 'down', components: {}, lastChecked: Date.now() })
    }
  },
}))
