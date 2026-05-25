import client from './client'
import type { RegisterRequest, LoginRequest, TokenResponse, MeResponse } from '@/types/auth'

export async function postRegister(req: RegisterRequest): Promise<TokenResponse> {
  const { data } = await client.post<TokenResponse>('/api/v1/auth/register', req)
  return data
}

export async function postLogin(req: LoginRequest): Promise<TokenResponse> {
  const { data } = await client.post<TokenResponse>('/api/v1/auth/login', req)
  return data
}

export async function getMe(): Promise<MeResponse> {
  const { data } = await client.get<MeResponse>('/api/v1/auth/me')
  return data
}
