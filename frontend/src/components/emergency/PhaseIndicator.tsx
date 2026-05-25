import { cn } from '@/lib/cn'
import { Search, MessageSquare, Send } from 'lucide-react'

interface PhaseIndicatorProps {
  phase: 'collecting' | 'clarifying' | 'dispatched'
}

const steps = [
  { key: 'collecting', label: '信息收集', icon: Search },
  { key: 'clarifying', label: '信息确认', icon: MessageSquare },
  { key: 'dispatched', label: '应急调度', icon: Send },
]

export function PhaseIndicator({ phase }: PhaseIndicatorProps) {
  const currentIndex = steps.findIndex((s) => s.key === phase)

  return (
    <div className="flex items-center gap-2 px-4 py-3 bg-card border-b border-border">
      {steps.map((step, i) => {
        const Icon = step.icon
        const isActive = i === currentIndex
        const isDone = i < currentIndex

        return (
          <div key={step.key} className="flex items-center gap-2 flex-1">
            <div
              className={cn(
                'w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium shrink-0 transition-colors',
                isDone && 'bg-success text-white',
                isActive && 'bg-primary text-primary-foreground ring-2 ring-primary/30',
                !isDone && !isActive && 'bg-secondary text-muted-foreground'
              )}
            >
              {isDone ? '✓' : <Icon className="w-3.5 h-3.5" />}
            </div>
            <span
              className={cn(
                'text-xs font-medium hidden sm:inline',
                isActive ? 'text-foreground' : 'text-muted-foreground'
              )}
            >
              {step.label}
            </span>
            {i < steps.length - 1 && (
              <div className={cn('flex-1 h-px mx-2', isDone ? 'bg-success' : 'bg-border')} />
            )}
          </div>
        )
      })}
    </div>
  )
}
