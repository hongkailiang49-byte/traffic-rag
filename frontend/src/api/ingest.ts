import client from './client'
import type { IngestRequest, IngestResponse } from '@/types/api'

export async function postIngest(req: IngestRequest = {}): Promise<IngestResponse> {
  const { data } = await client.post<IngestResponse>('/api/v1/ingest', req)
  return data
}
