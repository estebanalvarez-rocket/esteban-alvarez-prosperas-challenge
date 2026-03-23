import { createContext } from "react"

export interface TokenResponse {
  access_token: string
}

export interface AuthContextValue {
  token: string | null
  isAuthenticated: boolean
  loading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  clearError: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
