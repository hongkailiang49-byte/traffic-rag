import client from './client'
import type { SessionRequest, SessionResponse } from '@/types/api'

export async function postSessionMessage(req: SessionRequest): Promise<SessionResponse> {
  const { data } = await client.post<SessionResponse>('/api/v1/session/message', req)
  return data
}
