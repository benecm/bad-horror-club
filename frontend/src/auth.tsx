import { useQueryClient } from '@tanstack/react-query'
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { getToken, setToken, setUnauthorizedHandler, type UserOut } from './api/client'
import { useMe } from './api/queries'

interface AuthState {
  user: UserOut | undefined
  signIn: (token: string) => void
  signOut: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient()
  const [token, setTokenState] = useState<string | null>(getToken)
  const me = useMe(token !== null)

  const signOut = useCallback(() => {
    setToken(null)
    setTokenState(null)
    qc.clear()
  }, [qc])

  const signIn = useCallback(
    (newToken: string) => {
      setToken(newToken)
      qc.clear()
      setTokenState(newToken)
    },
    [qc],
  )

  useEffect(() => setUnauthorizedHandler(signOut), [signOut])

  // A stored token that the server rejects (expired, user deleted): drop it.
  useEffect(() => {
    if (me.isError && token) signOut()
  }, [me.isError, token, signOut])

  const value = useMemo(
    () => ({ user: token ? me.data : undefined, signIn, signOut }),
    [token, me.data, signIn, signOut],
  )
  return <AuthContext value={value}>{children}</AuthContext>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const location = useLocation()
  if (getToken() === null) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  if (!user) return <p className="p-8 text-dust">Opening the door…</p>
  return children
}
