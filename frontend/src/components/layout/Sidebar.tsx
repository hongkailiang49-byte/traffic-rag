import { NavLink } from 'react-router-dom'
import { MessageSquare, AlertTriangle, Database, X, Plus, Trash2, Clock } from 'lucide-react'
import * as ScrollArea from '@radix-ui/react-scroll-area'
import { cn } from '@/lib/cn'
import { useChatStore } from '@/stores/chatStore'

interface SidebarProps {
  open: boolean
  onClose: () => void
}

const navItems = [
  { to: '/', label: '智能问答', icon: MessageSquare },
  { to: '/emergency', label: '应急调度', icon: AlertTriangle },
  { to: '/admin', label: '数据管理', icon: Database },
]

function formatTime(iso: string) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH}小时前`
  const diffD = Math.floor(diffH / 24)
  if (diffD < 7) return `${diffD}天前`
  return `${d.getMonth() + 1}/${d.getDate()}`
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const { sessions, sessionId, clearMessages, loadSession, deleteSession } = useChatStore()

  const handleNewChat = () => {
    clearMessages()
    onClose()
  }

  const handleSelectSession = (sid: string) => {
    if (sid !== sessionId) {
      loadSession(sid)
    }
    onClose()
  }

  const handleDeleteSession = (e: React.MouseEvent, sid: string) => {
    e.stopPropagation()
    if (confirm('确定删除这个会话吗？')) {
      deleteSession(sid)
    }
  }

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={cn(
          'fixed lg:static inset-y-0 left-0 z-50 w-64 bg-card border-r border-border flex flex-col transition-transform duration-200 lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="h-14 flex items-center justify-between px-4 border-b border-border lg:hidden">
          <span className="font-semibold">导航</span>
          <button onClick={onClose} className="p-1 rounded hover:bg-accent">
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="p-3 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )
              }
            >
              <Icon className="w-5 h-5 shrink-0" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="px-3 pb-2">
          <button
            onClick={handleNewChat}
            className="flex items-center gap-2 w-full px-3 py-2.5 rounded-lg text-sm font-medium border border-dashed border-border text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
          >
            <Plus className="w-4 h-4" />
            新建对话
          </button>
        </div>

        <div className="px-3 pb-1">
          <div className="flex items-center gap-2 px-2 text-xs text-muted-foreground">
            <Clock className="w-3 h-3" />
            <span>历史会话</span>
          </div>
        </div>

        <ScrollArea.Root className="flex-1 overflow-hidden">
          <ScrollArea.Viewport className="h-full w-full px-3">
            {sessions.length === 0 ? (
              <p className="px-2 py-4 text-xs text-muted-foreground text-center">
                暂无历史会话
              </p>
            ) : (
              <div className="space-y-1 pb-3">
                {sessions.map((s) => (
                  <div
                    key={s.session_id}
                    onClick={() => handleSelectSession(s.session_id)}
                    className={cn(
                      'group flex items-start gap-2 px-2 py-2.5 rounded-lg text-sm cursor-pointer transition-colors',
                      s.session_id === sessionId
                        ? 'bg-accent text-accent-foreground'
                        : 'text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground'
                    )}
                  >
                    <MessageSquare className="w-4 h-4 shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="truncate text-xs leading-snug">
                        {s.first_message || s.session_id}
                      </p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">
                        {formatTime(s.created_at)} · {s.message_count}条消息
                      </p>
                    </div>
                    <button
                      onClick={(e) => handleDeleteSession(e, s.session_id)}
                      className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-destructive/10 hover:text-destructive transition-all shrink-0"
                      aria-label="删除会话"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea.Viewport>
          <ScrollArea.Scrollbar
            className="flex select-none touch-none p-0.5 bg-transparent transition-colors data-[orientation=vertical]:w-2"
            orientation="vertical"
          >
            <ScrollArea.Thumb className="flex-1 bg-border rounded-full" />
          </ScrollArea.Scrollbar>
        </ScrollArea.Root>

        <div className="p-4 border-t border-border text-xs text-muted-foreground">
          Traffic RAG v1.0
        </div>
      </aside>
    </>
  )
}
