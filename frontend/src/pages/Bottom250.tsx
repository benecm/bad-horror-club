import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { errorMessage } from '../api/client'
import type { Schemas } from '../api/client'
import { useAddFilm, useBottom250, useMarkWatched, useTmdbSearch } from '../api/queries'
import { ErrorText, Loading, Poster } from '../components/bits'

type Entry = Schemas['Bottom250Entry']

const ROLL_MS = 1100
const TICK_MS = 70

function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function statusLabel(status: Entry['status']): string | null {
  return status === 'watched' ? 'Watched' : status === 'watchlist' ? 'On the watchlist' : null
}

export function Bottom250() {
  const { data, isPending, error } = useBottom250()
  const [skipWatched, setSkipWatched] = useState(true)
  const [selected, setSelected] = useState<number | null>(null)
  const [shown, setShown] = useState<number | null>(null) // number on the "dice" while rolling
  const [rolling, setRolling] = useState(false)
  const [filter, setFilter] = useState('')
  const timer = useRef<number | undefined>(undefined)
  const panel = useRef<HTMLElement>(null)

  useEffect(() => () => window.clearInterval(timer.current), [])

  const films = useMemo(() => data?.films ?? [], [data])
  const current = films.find((f) => f.position === selected)
  const eligible = films.filter((f) => !(skipWatched && f.status === 'watched'))

  function roll() {
    if (eligible.length === 0 || rolling) return
    const landed = eligible[Math.floor(Math.random() * eligible.length)]
    if (prefersReducedMotion()) {
      setSelected(landed.position)
      setShown(landed.position)
      return
    }
    setRolling(true)
    setSelected(null)
    const started = Date.now()
    timer.current = window.setInterval(() => {
      if (Date.now() - started >= ROLL_MS) {
        window.clearInterval(timer.current)
        setShown(landed.position)
        setSelected(landed.position)
        setRolling(false)
      } else {
        setShown(1 + Math.floor(Math.random() * films.length))
      }
    }, TICK_MS)
  }

  function select(position: number) {
    window.clearInterval(timer.current)
    setRolling(false)
    setSelected(position)
    setShown(position)
    panel.current?.scrollIntoView({ block: 'nearest' })
  }

  const q = filter.trim().toLowerCase()
  const visible = q
    ? films.filter((f) => f.title.toLowerCase().includes(q) || String(f.position) === q)
    : films

  return (
    <section>
      <h1 className="text-5xl">Bottom 250</h1>
      <p className="mt-2 max-w-prose text-dust">
        Letterboxd’s 250 worst horror films. Roll a number and watch whatever it lands on.
      </p>

      {isPending && <Loading what="the list" />}
      {error && <ErrorText>{errorMessage(error)}</ErrorText>}

      {data && (
        <>
          <section ref={panel} className="mt-6 grid gap-4 rounded bg-shelf p-5" aria-live="polite">
            <div className="flex flex-wrap items-center gap-4">
              <button type="button" className="btn" onClick={roll} disabled={rolling || eligible.length === 0}>
                {rolling ? 'Rolling…' : selected ? 'Roll again' : 'Roll a number'}
              </button>
              <span
                className="sticker min-w-20 text-center text-4xl"
                aria-label={shown ? `Number ${shown}` : 'No number yet'}
              >
                {shown ?? '?'}
              </span>
              <label className="flex items-center gap-2 text-sm text-dust">
                <input
                  type="checkbox"
                  className="size-4 accent-blood"
                  checked={skipWatched}
                  onChange={(e) => setSkipWatched(e.target.checked)}
                />
                Skip films we’ve already watched
              </label>
            </div>
            {eligible.length === 0 && (
              <p className="text-dust">You’ve watched the whole list. Untick the box to roll again.</p>
            )}
            {current && <Result key={current.position} entry={current} />}
          </section>

          <div className="mt-8">
            <h2 className="text-3xl">The whole list</h2>
            <p className="mt-1 text-sm text-dust">
              Snapshot from {data.fetched_on}. The list on{' '}
              <a href={data.source} className="underline hover:text-bone" target="_blank" rel="noreferrer">
                Letterboxd
              </a>{' '}
              changes every week.
            </p>
            <label className="mt-4 block">
              <span className="sr-only">Find a film or number</span>
              <input
                className="field"
                placeholder="Find a title or a number"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                type="search"
              />
            </label>
            {visible.length === 0 ? (
              <p className="mt-4 text-dust">Nothing matches “{filter.trim()}”.</p>
            ) : (
              <ol className="mt-4 grid grid-cols-[minmax(0,1fr)] gap-1">
                {visible.map((f) => (
                  <li
                    key={f.position}
                    className={`flex items-center gap-3 rounded px-3 py-2 ${
                      f.position === selected ? 'bg-shelf-hi ring-1 ring-blood' : 'bg-shelf'
                    }`}
                  >
                    <span className="w-9 shrink-0 text-right font-bold tabular-nums text-blood">
                      {f.position}
                    </span>
                    <button
                      type="button"
                      onClick={() => select(f.position)}
                      className="min-w-0 flex-1 truncate text-left hover:underline"
                    >
                      {f.title} <span className="text-dust">({f.year})</span>
                    </button>
                    {statusLabel(f.status) && (
                      <span className="shrink-0 rounded-full bg-tape px-2 py-0.5 text-xs text-dust">
                        {statusLabel(f.status)}
                      </span>
                    )}
                  </li>
                ))}
              </ol>
            )}
          </div>
        </>
      )}
    </section>
  )
}

function Result({ entry }: { entry: Entry }) {
  const navigate = useNavigate()
  const add = useAddFilm()
  const markWatched = useMarkWatched()
  // Find a poster on TMDB; only trust a result from the same year.
  const search = useTmdbSearch(entry.title)
  const match = search.data?.find((r) => r.year === entry.year)

  function addFilm(status: 'watchlist' | 'watched') {
    add.mutate(
      {
        title: entry.title,
        year: entry.year,
        poster_url: match?.poster_url ?? null,
        tmdb_id: match?.tmdb_id ?? null,
        status,
      },
      { onSuccess: (film) => status === 'watched' && navigate(`/films/${film.id}`) },
    )
  }

  const busy = add.isPending || markWatched.isPending
  const justAdded = add.isSuccess && entry.status === 'watchlist'

  return (
    <div className="flex gap-4">
      <Poster title={entry.title} url={match?.poster_url} className="h-36 w-24" />
      <div className="min-w-0 flex-1">
        <p className="text-sm text-dust">Number {entry.position} of 250</p>
        <p className="text-2xl font-semibold">
          {entry.title} <span className="font-normal text-dust">({entry.year})</span>
        </p>
        <p className="mt-1 text-sm">
          <a
            href={entry.letterboxd_url}
            target="_blank"
            rel="noreferrer"
            className="text-dust underline hover:text-bone"
          >
            See it on Letterboxd
          </a>
        </p>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          {entry.status === 'watched' && entry.film_id && (
            <>
              <span className="text-dust">You’ve already watched this one.</span>
              <Link to={`/films/${entry.film_id}`} className="btn btn-quiet">
                Open the film
              </Link>
            </>
          )}
          {entry.status === 'watchlist' && entry.film_id && (
            <>
              <span className="text-dust">{justAdded ? 'Added to the watchlist.' : 'Already on the watchlist.'}</span>
              <button
                type="button"
                className="btn"
                disabled={busy}
                onClick={() =>
                  markWatched.mutate(entry.film_id!, {
                    onSuccess: () => navigate(`/films/${entry.film_id}`),
                  })
                }
              >
                We’re watching it tonight
              </button>
            </>
          )}
          {entry.status === null && (
            <>
              <button type="button" className="btn" disabled={busy} onClick={() => addFilm('watched')}>
                We’re watching it tonight
              </button>
              <button
                type="button"
                className="btn btn-quiet"
                disabled={busy}
                onClick={() => addFilm('watchlist')}
              >
                Add to watchlist
              </button>
            </>
          )}
        </div>
        <div className="mt-3 grid gap-2">
          <ErrorText>{add.isError ? errorMessage(add.error) : null}</ErrorText>
          <ErrorText>{markWatched.isError ? errorMessage(markWatched.error) : null}</ErrorText>
        </div>
      </div>
    </div>
  )
}
