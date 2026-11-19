import createClient, { type Middleware } from 'openapi-fetch'
import type { components, paths } from './schema'

export const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const TOKEN_KEY = 'bhc_token'

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* storage unavailable: the user just has to log in again next time */
  }
}

/** Called when the API says our token is no longer valid. */
let onUnauthorized: () => void = () => {}
export function setUnauthorizedHandler(fn: () => void): void {
  onUnauthorized = fn
}

const authMiddleware: Middleware = {
  onRequest({ request }) {
    const token = getToken()
    if (token) request.headers.set('Authorization', `Bearer ${token}`)
    return request
  },
  onResponse({ response, request }) {
    // A 401 on login/register is just "wrong password", not an expired session.
    const isAuthAttempt = /\/api\/auth\/(login|register)$/.test(new URL(request.url).pathname)
    if (response.status === 401 && !isAuthAttempt) onUnauthorized()
    return response
  },
}

export const api = createClient<paths>({ baseUrl: API_URL })
api.use(authMiddleware)

export type Schemas = components['schemas']
export type FilmOut = Schemas['FilmOut']
export type FilmDetail = Schemas['FilmDetail']
export type RankedFilm = Schemas['RankedFilm']
export type RatingOut = Schemas['RatingOut']
export type StatsOut = Schemas['StatsOut']
export type UserOut = Schemas['UserOut']
export type SortMode = 'badness' | 'fun' | 'combined'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function describe(error: unknown): string {
  if (error && typeof error === 'object' && 'detail' in error) {
    const detail = (error as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail
        .map((d: { loc?: unknown[]; msg?: string }) => {
          const field = d.loc?.filter((p) => p !== 'body').join('.')
          return field ? `${field}: ${d.msg}` : (d.msg ?? 'Invalid input')
        })
        .join('; ')
    }
  }
  return 'Something went wrong. Try again.'
}

/** Turns an openapi-fetch result into data, or throws an ApiError with a readable message. */
export async function unwrap<T>(
  request: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  const { data, error, response } = await request
  if (error !== undefined) throw new ApiError(describe(error), response.status)
  return data as T
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof TypeError) return "Can't reach the server. Check your connection."
  return 'Something went wrong. Try again.'
}
