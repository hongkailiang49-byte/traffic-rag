import { useState } from 'react'
import { postIngest } from '@/api/ingest'
import type { IngestResponse } from '@/types/api'
import { Database, FolderOpen, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import { cn } from '@/lib/cn'

export function IngestPanel() {
  const [directory, setDirectory] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<IngestResponse | null>(null)
  const [error, setError] = useState('')

  const handleIngest = async () => {
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await postIngest({ directory: directory || undefined })
      setResult(res)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '入库失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Database className="w-6 h-6 text-primary" />
          数据入库管理
        </h2>
        <p className="text-sm text-muted-foreground">
          触发知识文档的解析、切片、向量化和入库流程
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">数据目录</label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <FolderOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                value={directory}
                onChange={(e) => setDirectory(e.target.value)}
                placeholder="留空使用默认目录 (./rag_information)"
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-input bg-background text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <button
              onClick={handleIngest}
              disabled={loading}
              className={cn(
                'px-6 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium transition-colors',
                'hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2'
              )}
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4" />}
              {loading ? '入库中...' : '开始入库'}
            </button>
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
            <XCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        {result && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 p-4 rounded-lg bg-success/10 border border-success/20 text-success text-sm">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              {result.message}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: '总文件数', value: result.total_files },
                { label: '总切片数', value: result.total_chunks },
                { label: '成功文件', value: result.success_files },
                { label: '失败文件', value: result.failed_files.length },
              ].map(({ label, value }) => (
                <div key={label} className="p-3 rounded-lg border border-border bg-card text-center">
                  <p className="text-2xl font-bold text-primary">{value}</p>
                  <p className="text-xs text-muted-foreground mt-1">{label}</p>
                </div>
              ))}
            </div>

            {result.failed_files.length > 0 && (
              <div className="p-3 rounded-lg border border-warning/30 bg-warning/5">
                <p className="text-xs font-medium text-warning mb-2">失败文件：</p>
                {result.failed_files.map((f) => (
                  <p key={f} className="text-xs text-muted-foreground">{f}</p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
