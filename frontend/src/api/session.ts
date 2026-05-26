import client from './client'
import type { SessionRequest, SessionResponse, SessionOut, MessageOut } from '@/types/api'

export async function postSessionMessage(req: SessionRequest): Promise<SessionResponse> {
  const { data } = await client.post<SessionResponse>('/api/v1/session/message', req)
  return data
}

export async function getSessions(): Promise<SessionOut[]> {
  const { data } = await client.get<SessionOut[]>('/api/v1/sessions')
  return data
}

export async function getSessionMessages(sessionId: string): Promise<MessageOut[]> {
  const { data } = await client.get<MessageOut[]>(`/api/v1/sessions/${sessionId}/messages`)
  return data
}

export async function deleteSession(sessionId: string): Promise<void> {
  await client.delete(`/api/v1/sessions/${sessionId}`)
}
