import { useState, useEffect } from 'react'
import { ChatPanel } from '@/components/chat/ChatPanel'
import { SourcePanel } from '@/components/sources/SourcePanel'
import { FileText } from 'lucide-react'
import { useChatStore } from '@/stores/chatStore'

export function ChatPage() {
  const [sourceOpen, setSourceOpen] = useState(false)
  const lastSources = useChatStore((s) => s.lastSources)
  const loadSessions = useChatStore((s) => s.loadSessions)

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  return (
    <div className="flex h-full relative">
      <div className="flex-1 min-w-0">
        <ChatPanel />
      </div>

      <SourcePanel visible={sourceOpen} onClose={() => setSourceOpen(false)} />

      {!sourceOpen && lastSources.length > 0 && (
        <button
          onClick={() => setSourceOpen(true)}
          className="fixed bottom-24 right-4 xl:hidden p-3 rounded-full bg-primary text-primary-foreground shadow-lg z-30"
          aria-label="查看来源"
        >
          <FileText className="w-5 h-5" />
          <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-destructive text-destructive-foreground text-xs flex items-center justify-center">
            {lastSources.length}
          </span>
        </button>
      )}
    </div>
  )
}
