import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { api, errorMessage, getToken, unwrap } from '../api/client'
import { useAuth } from '../auth'
import { ErrorText } from '../components/bits'

export function Login() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/'

  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [joinCode, setJoinCode] = useState('')

  const submit = useMutation({
    mutationFn: async () => {
      if (mode === 'register') {
        await unwrap(
          api.POST('/api/auth/register', {
            body: {
              username,
              display_name: displayName,
              password,
              join_code: joinCode,
            },
          }),
        )
      }
      return unwrap(api.POST('/api/auth/login', { body: { username, password } }))
    },
    onSuccess: (data) => {
      signIn(data.access_token)
      navigate(from, { replace: true })
    },
  })

  if (getToken()) return <Navigate to="/" replace />

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    submit.mutate()
  }

  const registering = mode === 'register'

  return (
    <main className="mx-auto grid min-h-dvh max-w-sm content-center gap-6 px-4 py-10">
      <div>
        <h1 className="text-6xl text-blood">Bad Horror Club</h1>
        <p className="mt-3 text-dust">
          {registering
            ? 'Ask the club for the join code, then pick a name.'
            : 'Sign in to rate tonight’s worst.'}
        </p>
      </div>

      <form onSubmit={onSubmit} className="grid gap-4">
        <label className="grid gap-1">
          <span className="text-sm text-dust">Username</span>
          <input
            className="field"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoCapitalize="none"
            required
            minLength={3}
          />
        </label>
        {registering && (
          <label className="grid gap-1">
            <span className="text-sm text-dust">Display name</span>
            <input
              className="field"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
            />
          </label>
        )}
        <label className="grid gap-1">
          <span className="text-sm text-dust">
            {registering ? 'Password (at least 8 characters)' : 'Password'}
          </span>
          <input
            className="field"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={registering ? 'new-password' : 'current-password'}
            required
            minLength={registering ? 8 : undefined}
          />
        </label>
        {registering && (
          <label className="grid gap-1">
            <span className="text-sm text-dust">Join code</span>
            <input
              className="field"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value)}
              autoComplete="off"
              required
            />
          </label>
        )}

        <ErrorText>{submit.isError ? errorMessage(submit.error) : null}</ErrorText>

        <button type="submit" className="btn" disabled={submit.isPending}>
          {submit.isPending ? 'One moment…' : registering ? 'Create account' : 'Sign in'}
        </button>
      </form>

      <button
        type="button"
        className="text-left text-sm text-dust underline hover:text-bone"
        onClick={() => {
          submit.reset()
          setMode(registering ? 'login' : 'register')
        }}
      >
        {registering ? 'I already have an account' : 'I have a join code'}
      </button>
    </main>
  )
}
