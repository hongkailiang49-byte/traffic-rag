import { CheckCircle2, Circle } from 'lucide-react'
import { cn } from '@/lib/cn'

interface SlotCardProps {
  label: string
  value?: string
  isMissing: boolean
}

export function SlotCard({ label, value, isMissing }: SlotCardProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-colors',
        isMissing
          ? 'border-dashed border-border bg-background'
          : 'border-success/30 bg-success/5'
      )}
    >
      {isMissing ? (
        <Circle className="w-4 h-4 text-muted-foreground shrink-0" />
      ) : (
        <CheckCircle2 className="w-4 h-4 text-success shrink-0" />
      )}
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium">{label}</p>
        <p className={cn('text-xs truncate', isMissing ? 'text-muted-foreground' : 'text-foreground')}>
          {isMissing ? '待收集' : value}
        </p>
      </div>
    </div>
  )
}
