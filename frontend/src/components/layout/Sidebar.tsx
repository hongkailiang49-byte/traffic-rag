import { NavLink } from 'react-router-dom'
import { MessageSquare, AlertTriangle, Database, X } from 'lucide-react'
import { cn } from '@/lib/cn'

interface SidebarProps {
  open: boolean
  onClose: () => void
}

const navItems = [
  { to: '/', label: '智能问答', icon: MessageSquare },
  { to: '/emergency', label: '应急调度', icon: AlertTriangle },
  { to: '/admin', label: '数据管理', icon: Database },
]

export function Sidebar({ open, onClose }: SidebarProps) {
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
          'fixed lg:static inset-y-0 left-0 z-50 w-60 bg-card border-r border-border flex flex-col transition-transform duration-200 lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="h-14 flex items-center justify-between px-4 border-b border-border lg:hidden">
          <span className="font-semibold">导航</span>
          <button onClick={onClose} className="p-1 rounded hover:bg-accent">
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 p-3 space-y-1">
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

        <div className="p-4 border-t border-border text-xs text-muted-foreground">
          Traffic RAG v1.0
        </div>
      </aside>
    </>
  )
}
