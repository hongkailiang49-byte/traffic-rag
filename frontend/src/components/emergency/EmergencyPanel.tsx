import { useEffect, useRef } from 'react'
import { useEmergencyStore } from '@/stores/emergencyStore'
import { PhaseIndicator } from './PhaseIndicator'
import { SlotCard } from './SlotCard'
import { MessageBubble } from '@/components/chat/MessageBubble'
import { ChatInput } from '@/components/chat/ChatInput'
import { SLOT_LABELS, INTENT_SLOTS, INTENT_LABELS } from '@/constants/emergency'
import { AlertTriangle, RotateCcw, Bot } from 'lucide-react'

export function EmergencyPanel() {
  const { phase, intent, collectedSlots, missingSlots, messages, isLoading, sendMessage, reset, dispatchOrder } =
    useEmergencyStore()
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }
  }, [messages, isLoading])

  const requiredSlots = INTENT_SLOTS[intent] || INTENT_SLOTS.accident

  return (
    <div className="flex flex-col h-full">
      <PhaseIndicator phase={phase} />

      <div className="flex flex-1 overflow-hidden">
        <div className="w-64 border-r border-border p-3 overflow-y-auto hidden md:block space-y-2 shrink-0">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-emergency" />
              {INTENT_LABELS[intent] || '事件信息'}
            </h3>
            <button
              onClick={reset}
              className="p-1 rounded hover:bg-accent text-muted-foreground"
              aria-label="重置"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>

          {requiredSlots.map((slotKey) => (
            <SlotCard
              key={slotKey}
              label={SLOT_LABELS[slotKey] || slotKey}
              value={collectedSlots[slotKey]}
              isMissing={missingSlots.includes(slotKey) || !collectedSlots[slotKey]}
            />
          ))}

          {phase === 'dispatched' && dispatchOrder && (
            <div className="mt-4 p-3 rounded-lg bg-success/10 border border-success/20">
              <p className="text-xs font-medium text-success mb-1">调度指令已生成</p>
              <p className="text-xs text-muted-foreground line-clamp-4">{dispatchOrder}</p>
            </div>
          )}
        </div>

        <div className="flex-1 flex flex-col min-w-0">
          <div ref={listRef} className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-3">
                <AlertTriangle className="w-14 h-14 opacity-30 text-emergency" />
                <div className="text-center">
                  <p className="text-lg font-medium">应急调度模式</p>
                  <p className="text-sm mt-1">描述紧急事件，系统将逐步收集信息并生成调度指令</p>
                </div>
                <div className="flex flex-wrap gap-2 justify-center max-w-md">
                  {['京藏高速发生追尾事故，有人员受伤', '隧道内发生火灾，需要紧急疏散', '高速公路上有车辆故障'].map((q) => (
                    <button
                      key={q}
                      onClick={() => sendMessage(q)}
                      className="px-3 py-2 text-xs rounded-lg border border-border hover:bg-accent transition-colors text-left"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
            )}

            {isLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-emergency/10 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-emergency" />
                </div>
                <div className="bg-card border border-border rounded-xl px-4 py-3">
                  <div className="flex gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-emergency/40 animate-bounce [animation-delay:0ms]" />
                    <div className="w-2 h-2 rounded-full bg-emergency/40 animate-bounce [animation-delay:150ms]" />
                    <div className="w-2 h-2 rounded-full bg-emergency/40 animate-bounce [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}
          </div>

          <ChatInput
            onSend={sendMessage}
            disabled={isLoading || phase === 'dispatched'}
            placeholder={phase === 'dispatched' ? '调度指令已生成，点击重置开始新的事件' : '描述紧急事件情况...'}
          />
        </div>
      </div>
    </div>
  )
}
