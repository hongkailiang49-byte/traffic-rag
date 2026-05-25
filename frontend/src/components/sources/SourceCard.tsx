import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { Source } from '@/types/api'

interface SourceCardProps {
  source: Source
  index: number
}

export function SourceCard({ source, index }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false)
  const scorePercent = Math.round(source.score * 100)

  const scoreColor =
    scorePercent >= 90 ? 'bg-success' : scorePercent >= 70 ? 'bg-primary' : 'bg-warning'

  return (
    <div className="rounded-lg border border-border p-3 space-y-2 hover:border-primary/30 transition-colors">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">#{index + 1}</span>
        <span className="text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground">
          {source.source}
        </span>
      </div>

      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">相关度</span>
          <span className="font-medium">{scorePercent}%</span>
        </div>
        <div className="w-full h-1.5 rounded-full bg-secondary overflow-hidden">
          <div className={cn('h-full rounded-full transition-all', scoreColor)} style={{ width: `${scorePercent}%` }} />
        </div>
      </div>

      <div className="text-xs text-muted-foreground">
        <p className={cn(!expanded && 'line-clamp-3')}>{source.content}</p>
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 mt-1 text-primary hover:underline"
        >
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          {expanded ? '收起' : '展开全部'}
        </button>
      </div>
    </div>
  )
}
