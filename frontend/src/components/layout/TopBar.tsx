import { useThemeStore } from '@/stores/themeStore'
import { useHealthStore } from '@/stores/healthStore'
import { useAuthStore } from '@/stores/authStore'
import { Moon, Sun, Activity, Menu, LogOut, User } from 'lucide-react'
import { cn } from '@/lib/cn'

interface TopBarProps {
  onMenuClick: () => void
}

export function TopBar({ onMenuClick }: TopBarProps) {
  const { theme, toggle } = useThemeStore()
  const { status } = useHealthStore()
  const { user, logout } = useAuthStore()

  const statusColor = {
    ok: 'bg-success',
    degraded: 'bg-warning',
    down: 'bg-destructive',
  }[status]

  const statusText = {
    ok: '系统正常',
    degraded: '部分降级',
    down: '连接失败',
  }[status]

  return (
    <header className="h-14 border-b border-border bg-card flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-md hover:bg-accent transition-colors"
          aria-label="打开菜单"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary" />
          <h1 className="text-base font-semibold hidden sm:block">交通领域 RAG 智能问答系统</h1>
          <h1 className="text-base font-semibold sm:hidden">RAG 问答</h1>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className={cn('w-2 h-2 rounded-full', statusColor)} />
          <span className="hidden sm:inline">{statusText}</span>
        </div>

        <button
          onClick={toggle}
          className="p-2 rounded-md hover:bg-accent transition-colors"
          aria-label="切换主题"
        >
          {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
        </button>

        {user && (
          <div className="flex items-center gap-2 pl-2 border-l border-border">
            <div className="flex items-center gap-2 text-sm">
              <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="w-3.5 h-3.5 text-primary" />
              </div>
              <span className="hidden md:inline font-medium">{user.name}</span>
            </div>
            <button
              onClick={logout}
              className="p-2 rounded-md hover:bg-accent transition-colors text-muted-foreground hover:text-destructive"
              aria-label="退出登录"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
