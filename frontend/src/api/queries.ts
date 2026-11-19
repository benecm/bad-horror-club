import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, unwrap, type SortMode } from './client'

export const keys = {
  me: ['me'] as const,
  rankings: (sort: SortMode) => ['rankings', sort] as const,
  films: (status?: 'watchlist' | 'watched') => ['films', status ?? 'all'] as const,
  film: (id: number) => ['film', id] as const,
  stats: ['stats'] as const,
}

export function useMe(enabled: boolean) {
  return useQuery({
    queryKey: keys.me,
    queryFn: () => unwrap(api.GET('/api/auth/me')),
    enabled,
    retry: false,
  })
}

export function useRankings(sort: SortMode) {
  return useQuery({
    queryKey: keys.rankings(sort),
    queryFn: () => unwrap(api.GET('/api/rankings', { params: { query: { sort } } })),
  })
}

export function useFilms(status?: 'watchlist' | 'watched') {
  return useQuery({
    queryKey: keys.films(status),
    queryFn: () => unwrap(api.GET('/api/films', { params: { query: { status } } })),
  })
}

export function useFilm(id: number) {
  return useQuery({
    queryKey: keys.film(id),
    queryFn: () => unwrap(api.GET('/api/films/{film_id}', { params: { path: { film_id: id } } })),
    enabled: Number.isFinite(id),
  })
}

export function useStats() {
  return useQuery({
    queryKey: keys.stats,
    queryFn: () => unwrap(api.GET('/api/stats')),
  })
}

/** Anything a film change can affect: lists, rankings, stats. */
export function useInvalidateFilmData() {
  const qc = useQueryClient()
  return () =>
    Promise.all([
      qc.invalidateQueries({ queryKey: ['films'] }),
      qc.invalidateQueries({ queryKey: ['film'] }),
      qc.invalidateQueries({ queryKey: ['rankings'] }),
      qc.invalidateQueries({ queryKey: keys.stats }),
      qc.invalidateQueries({ queryKey: ['bottom250'] }),
    ])
}

export function useAddFilm() {
  const invalidate = useInvalidateFilmData()
  return useMutation({
    mutationFn: (body: {
      title: string
      year?: number | null
      poster_url?: string | null
      tmdb_id?: number | null
      status: 'watchlist' | 'watched'
      watched_on?: string | null
    }) => unwrap(api.POST('/api/films', { body })),
    onSuccess: invalidate,
  })
}

export function useMarkWatched() {
  const invalidate = useInvalidateFilmData()
  return useMutation({
    mutationFn: (id: number) =>
      unwrap(
        api.PATCH('/api/films/{film_id}', {
          params: { path: { film_id: id } },
          body: { status: 'watched' },
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useDeleteFilm() {
  const invalidate = useInvalidateFilmData()
  return useMutation({
    mutationFn: (id: number) =>
      unwrap(api.DELETE('/api/films/{film_id}', { params: { path: { film_id: id } } })),
    onSuccess: invalidate,
  })
}

export function useSaveRating(filmId: number) {
  const invalidate = useInvalidateFilmData()
  return useMutation({
    mutationFn: (body: { badness: number; fun: number; comment: string | null }) =>
      unwrap(
        api.PUT('/api/films/{film_id}/rating', {
          params: { path: { film_id: filmId } },
          body,
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useDeleteRating(filmId: number) {
  const invalidate = useInvalidateFilmData()
  return useMutation({
    mutationFn: () =>
      unwrap(
        api.DELETE('/api/films/{film_id}/rating', { params: { path: { film_id: filmId } } }),
      ),
    onSuccess: invalidate,
  })
}

export function useTmdbSearch(q: string) {
  return useQuery({
    queryKey: ['tmdb', q],
    queryFn: () => unwrap(api.GET('/api/tmdb/search', { params: { query: { q } } })),
    enabled: q.length >= 2,
    staleTime: 5 * 60_000,
    retry: false,
  })
}

export function useVote() {
  const invalidate = useInvalidateFilmData()
  return useMutation({
    mutationFn: ({ id, vote }: { id: number; vote: boolean }) =>
      vote
        ? unwrap(api.PUT('/api/films/{film_id}/vote', { params: { path: { film_id: id } } }))
        : unwrap(api.DELETE('/api/films/{film_id}/vote', { params: { path: { film_id: id } } })),
    onSuccess: invalidate,
  })
}

export function useAddQuote(filmId: number) {
  const invalidate = useInvalidateFilmData()
  return useMutation({
    mutationFn: (text: string) =>
      unwrap(
        api.POST('/api/films/{film_id}/quotes', {
          params: { path: { film_id: filmId } },
          body: { text },
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useDeleteQuote() {
  const invalidate = useInvalidateFilmData()
  return useMutation({
    mutationFn: (id: number) =>
      unwrap(api.DELETE('/api/quotes/{quote_id}', { params: { path: { quote_id: id } } })),
    onSuccess: invalidate,
  })
}

export function useBottom250() {
  return useQuery({
    queryKey: ['bottom250'],
    queryFn: () => unwrap(api.GET('/api/bottom250')),
    staleTime: 60_000,
  })
}
