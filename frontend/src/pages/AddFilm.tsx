import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { errorMessage } from '../api/client'
import type { Schemas } from '../api/client'
import { useAddFilm, useTmdbSearch } from '../api/queries'
import { ErrorText, Poster } from '../components/bits'
import { useDebounced } from '../hooks'

type TmdbResult = Schemas['TmdbResult']

export function AddFilm() {
  const navigate = useNavigate()
  const add = useAddFilm()
  const [search, setSearch] = useState('')
  const [picked, setPicked] = useState<TmdbResult | null>(null)
  const [title, setTitle] = useState('')
  const [year, setYear] = useState('')
  const [status, setStatus] = useState<'watchlist' | 'watched'>('watched')

  const debouncedSearch = useDebounced(search.trim())
  const results = useTmdbSearch(picked ? '' : debouncedSearch)

  function pick(r: TmdbResult) {
    setPicked(r)
    setTitle(r.title)
    setYear(r.year ? String(r.year) : '')
    setSearch('')
  }

  function clearPick() {
    setPicked(null)
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    add.mutate(
      {
        title,
        year: year ? Number(year) : null,
        poster_url: picked?.poster_url ?? null,
        tmdb_id: picked?.tmdb_id ?? null,
        status,
      },
      {
        onSuccess: (film) => navigate(status === 'watched' ? `/films/${film.id}` : '/watchlist'),
      },
    )
  }

  const searching = !picked && debouncedSearch.length >= 2

  return (
    <section className="max-w-lg">
      <h1 className="text-5xl">Add a film</h1>
      <form onSubmit={onSubmit} className="mt-6 grid gap-5">
        {picked ? (
          <div className="flex items-center gap-4 rounded bg-shelf p-3">
            <Poster title={picked.title} url={picked.poster_url} />
            <div className="min-w-0 flex-1">
              <p className="font-semibold">
                {picked.title}
                {picked.year ? <span className="font-normal text-dust"> ({picked.year})</span> : null}
              </p>
              <p className="text-sm text-dust">Details and poster from TMDB</p>
            </div>
            <button type="button" className="btn btn-quiet text-sm" onClick={clearPick}>
              Change
            </button>
          </div>
        ) : (
          <div className="grid gap-1">
            <label htmlFor="film-search" className="text-sm text-dust">
              Search for the film (optional)
            </label>
            <input
              id="film-search"
              className="field"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Start typing a title"
              autoComplete="off"
            />
            {searching && results.isFetching && <p className="text-sm text-dust">Searching…</p>}
            {searching && results.isError && (
              <p className="text-sm text-dust">
                {errorMessage(results.error)} You can still type the title below.
              </p>
            )}
            {searching && results.data && results.data.length === 0 && !results.isFetching && (
              <p className="text-sm text-dust">No matches. Type the title below instead.</p>
            )}
            {searching && results.data && results.data.length > 0 && (
              <ul className="mt-1 grid gap-1">
                {results.data.map((r) => (
                  <li key={r.tmdb_id}>
                    <button
                      type="button"
                      onClick={() => pick(r)}
                      className="flex w-full items-center gap-3 rounded bg-shelf p-2 text-left hover:bg-shelf-hi"
                    >
                      <Poster title={r.title} url={r.poster_url} className="h-14 w-10" />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-semibold">
                          {r.title}
                          {r.year ? <span className="font-normal text-dust"> ({r.year})</span> : null}
                        </span>
                        {r.overview && (
                          <span className="line-clamp-1 text-sm text-dust">{r.overview}</span>
                        )}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        <label className="grid gap-1">
          <span className="text-sm text-dust">Title</span>
          <input
            className="field"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            maxLength={300}
          />
        </label>
        <label className="grid gap-1">
          <span className="text-sm text-dust">Year (optional)</span>
          <input
            className="field w-32"
            type="number"
            inputMode="numeric"
            min={1888}
            max={2100}
            value={year}
            onChange={(e) => setYear(e.target.value)}
          />
        </label>
        <fieldset className="grid gap-2">
          <legend className="mb-1 text-sm text-dust">When is it happening?</legend>
          {(
            [
              ['watched', 'We watched it tonight'],
              ['watchlist', 'Save it for later'],
            ] as const
          ).map(([value, label]) => (
            <label key={value} className="flex items-center gap-3">
              <input
                type="radio"
                name="status"
                value={value}
                checked={status === value}
                onChange={() => setStatus(value)}
                className="size-4 accent-blood"
              />
              {label}
            </label>
          ))}
        </fieldset>
        <ErrorText>{add.isError ? errorMessage(add.error) : null}</ErrorText>
        <div>
          <button type="submit" className="btn" disabled={add.isPending}>
            {add.isPending ? 'Adding…' : status === 'watched' ? 'Add and rate it' : 'Add to watchlist'}
          </button>
        </div>
      </form>
    </section>
  )
}
