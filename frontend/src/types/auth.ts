export interface RegisterRequest {
  email: string
  name: string
  password: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: UserInfo
}

export interface UserInfo {
  email: string
  name: string
  clearance_level: number
}

export interface UserStats {
  total_queries: number
  intent_diversity: number
}

export interface MeResponse extends UserInfo {
  stats: UserStats
}
