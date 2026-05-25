import { useChatStore } from '@/stores/chatStore'
import { SourceCard } from './SourceCard'
import { FileText, X } from 'lucide-react'
import { cn } from '@/lib/cn'

interface SourcePanelProps {
  visible: boolean
  onClose: () => void
}

export function SourcePanel({ visible, onClose }: SourcePanelProps) {
  const { lastSources } = useChatStore()

  return (
    <>
      {visible && (
        <div className="fixed inset-0 bg-black/50 z-40 xl:hidden" onClick={onClose} />
      )}
      <aside
        className={cn(
          'fixed xl:static right-0 top-0 bottom-0 z-50 w-80 bg-card border-l border-border flex flex-col transition-transform duration-200 xl:translate-x-0',
          visible ? 'translate-x-0' : 'translate-x-full xl:translate-x-0'
        )}
      >
        <div className="h-14 flex items-center justify-between px-4 border-b border-border shrink-0">
          <div className="flex items-center gap-2 text-sm font-medium">
            <FileText className="w-4 h-4" />
            <span>参考来源</span>
            {lastSources.length > 0 && (
              <span className="px-1.5 py-0.5 rounded-full text-xs bg-primary/10 text-primary">
                {lastSources.length}
              </span>
            )}
          </div>
          <button onClick={onClose} className="xl:hidden p-1 rounded hover:bg-accent">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          {lastSources.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground text-sm">
              <FileText className="w-10 h-10 mb-2 opacity-30" />
              <p>暂无参考来源</p>
              <p className="text-xs mt-1">发送问题后将显示检索结果</p>
            </div>
          ) : (
            lastSources.map((source, i) => <SourceCard key={i} source={source} index={i} />)
          )}
        </div>
      </aside>
    </>
  )
}
