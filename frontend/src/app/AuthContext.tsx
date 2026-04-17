import { createContext, useContext, useEffect, useMemo, useState } from 'react'

import { authApi } from '../api/client'
import type { TokenResponse, User } from '../types/api'

type AuthContextValue = {
  token: string | null
  user: User | null
  loading: boolean
  setSession: (payload: TokenResponse) => void
  logout: () => void
}

const STORAGE_KEY = 'semantic-field-namer-token'

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem(STORAGE_KEY))
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const bootstrap = async () => {
      if (!token) {
        setLoading(false)
        return
      }
      try {
        const me = await authApi.me()
        setUser(me)
      } catch {
        localStorage.removeItem(STORAGE_KEY)
        setToken(null)
        setUser(null)
      } finally {
        setLoading(false)
      }
    }
    void bootstrap()
  }, [token])

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      loading,
      setSession: (payload) => {
        localStorage.setItem(STORAGE_KEY, payload.access_token)
        setToken(payload.access_token)
        setUser(payload.user)
      },
      logout: () => {
        localStorage.removeItem(STORAGE_KEY)
        setToken(null)
        setUser(null)
      },
    }),
    [loading, token, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return value
}
