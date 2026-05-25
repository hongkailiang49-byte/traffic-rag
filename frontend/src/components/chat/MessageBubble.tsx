import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { Bot, User, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { Message } from '@/types/chat'
import { INTENT_LABELS } from '@/constants/emergency'

interface MessageBubbleProps {
  message: Message
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'

  return (
    <div className={cn('flex gap-3', isUser ? 'flex-row-reverse' : 'flex-row')}>
      <div
        className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center shrink-0',
          isUser
            ? 'bg-primary text-primary-foreground'
            : isSystem
            ? 'bg-destructive text-destructive-foreground'
            : 'bg-secondary text-secondary-foreground'
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : isSystem ? <AlertCircle className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      <div
        className={cn(
          'max-w-[80%] rounded-xl px-4 py-3 text-sm',
          isUser
            ? 'bg-primary text-primary-foreground'
            : isSystem
            ? 'bg-destructive/10 text-destructive border border-destructive/20'
            : 'bg-card border border-border'
        )}
      >
        {message.intent && INTENT_LABELS[message.intent] && (
          <div className="mb-2">
            <span className="inline-block px-2 py-0.5 rounded text-xs bg-primary/10 text-primary font-medium">
              {INTENT_LABELS[message.intent] || message.intent}
            </span>
          </div>
        )}

        {isUser || isSystem ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none prose-table:block prose-table:overflow-x-auto">
            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        <div className={cn('text-xs mt-2', isUser ? 'text-primary-foreground/70' : 'text-muted-foreground')}>
          {new Date(message.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  )
}
