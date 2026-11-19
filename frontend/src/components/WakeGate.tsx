import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { API_URL } from '../api/client'

const RETRY_MS = 3000
const SHOW_AFTER_MS = 700

/**
 * The free backend sleeps when idle and takes up to a minute to wake.
 * Ping /api/health until it answers, and only show the waiting screen if that takes a moment.
 */
export function WakeGate({ children }: { children: ReactNode }) {
  const [awake, setAwake] = useState(false)
  const [showWaiting, setShowWaiting] = useState(false)
  const [attempts, setAttempts] = useState(0)

  useEffect(() => {
    if (awake) return
    const show = window.setTimeout(() => setShowWaiting(true), SHOW_AFTER_MS)
    const controller = new AbortController()
    let retry: number | undefined

    async function ping() {
      try {
        const res = await fetch(`${API_URL}/api/health`, {
          signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10_000)]),
        })
        if (res.ok) {
          setAwake(true)
          return
        }
      } catch {
        if (controller.signal.aborted) return
      }
      setAttempts((n) => n + 1)
      retry = window.setTimeout(ping, RETRY_MS)
    }
    void ping()

    return () => {
      controller.abort()
      window.clearTimeout(show)
      window.clearTimeout(retry)
    }
  }, [awake])

  if (awake) return children
  if (!showWaiting) return null

  return (
    <main className="grid min-h-dvh place-items-center px-6 text-center">
      <div role="status" aria-live="polite" className="max-w-sm">
        <h1 className="flicker text-5xl text-blood">Waking up the crypt…</h1>
        <p className="mt-4 text-dust">
          The server naps when nobody is around. This can take up to a minute.
        </p>
        {attempts >= 6 && (
          <p className="mt-3 text-sm text-dust">Still nothing. It's probably just a deep sleeper.</p>
        )}
      </div>
    </main>
  )
}
