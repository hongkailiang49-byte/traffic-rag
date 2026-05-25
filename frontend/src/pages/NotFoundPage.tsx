import { Link } from 'react-router-dom'
import { Home } from 'lucide-react'

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 text-center p-8">
      <p className="text-6xl font-bold text-muted-foreground/30">404</p>
      <h2 className="text-xl font-semibold">页面不存在</h2>
      <p className="text-muted-foreground text-sm">您访问的页面不存在或已被移除</p>
      <Link
        to="/"
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
      >
        <Home className="w-4 h-4" />
        返回首页
      </Link>
    </div>
  )
}
