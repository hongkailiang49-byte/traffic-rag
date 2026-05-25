import client from './client'
import type { QueryRequest, QueryResponse } from '@/types/api'

export async function postQuery(req: QueryRequest): Promise<QueryResponse> {
  const { data } = await client.post<QueryResponse>('/api/v1/query', req)
  return data
}
