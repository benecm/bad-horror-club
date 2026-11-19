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
    ])
}

export function useAddFilm() {
  const invalidate = useInvalidateFilmData()
  return useMutation({
    mutationFn: (body: {
      title: string
      year?: number | null
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
