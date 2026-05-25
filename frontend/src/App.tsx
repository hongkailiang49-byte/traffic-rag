import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { TopBar } from '@/components/layout/TopBar'
import { Sidebar } from '@/components/layout/Sidebar'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { ChatPage } from '@/pages/ChatPage'
import { EmergencyPage } from '@/pages/EmergencyPage'
import { AdminPage } from '@/pages/AdminPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { useHealthStore } from '@/stores/healthStore'

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const fetchHealth = useHealthStore((s) => s.fetchHealth)

  useEffect(() => {
    fetchHealth()
    const timer = setInterval(fetchHealth, 30000)
    return () => clearInterval(timer)
  }, [fetchHealth])

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="h-screen flex flex-col">
          <TopBar onMenuClick={() => setSidebarOpen(true)} />
          <div className="flex flex-1 overflow-hidden">
            <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
            <main className="flex-1 overflow-hidden">
              <Routes>
                <Route path="/" element={<ChatPage />} />
                <Route path="/emergency" element={<EmergencyPage />} />
                <Route path="/admin" element={<AdminPage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
