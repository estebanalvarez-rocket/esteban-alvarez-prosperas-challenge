import { type ReactNode, useEffect, useState } from "react"

import { apiRequest } from "../services/api"
import { AuthContext, type AuthContextValue, type TokenResponse } from "./authContext"

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => window.localStorage.getItem("reports-token"))
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (token) {
      window.localStorage.setItem("reports-token", token)
    } else {
      window.localStorage.removeItem("reports-token")
    }
  }, [token])

  const clearError = () => {
    setError(null)
  }

  const authenticate = async (mode: "login" | "register", email: string, password: string) => {
    try {
      setLoading(true)
      setError(null)

      if (mode === "register") {
        await apiRequest("/auth/register", "POST", { email, password })
      }

      const response = await apiRequest<TokenResponse>("/auth/login", "POST", { email, password })
      setToken(response.access_token)
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "No fue posible autenticarse")
      throw authError
    } finally {
      setLoading(false)
    }
  }

  const value: AuthContextValue = {
    token,
    isAuthenticated: Boolean(token),
    loading,
    error,
    login: async (email, password) => authenticate("login", email, password),
    register: async (email, password) => authenticate("register", email, password),
    logout: () => {
      setToken(null)
      setError(null)
    },
    clearError,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
