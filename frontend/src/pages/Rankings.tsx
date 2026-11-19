import { Link, useSearchParams } from 'react-router-dom'
import type { RankedFilm, SortMode } from '../api/client'
import { useRankings } from '../api/queries'
import { ErrorText, Loading, Poster, formatScore } from '../components/bits'
import { errorMessage } from '../api/client'

const TABS: { sort: SortMode; label: string; blurb: string }[] = [
  { sort: 'badness', label: 'Hall of shame', blurb: 'The most terrible films, worst first.' },
  { sort: 'fun', label: 'So bad it’s good', blurb: 'The films that were the most fun to sit through.' },
  { sort: 'combined', label: 'Combined', blurb: 'Badness and fun averaged together.' },
]

function parseSort(value: string | null): SortMode {
  return value === 'badness' || value === 'fun' || value === 'combined' ? value : 'badness'
}

function mainScore(film: RankedFilm, sort: SortMode): number {
  return sort === 'badness' ? film.avg_badness : sort === 'fun' ? film.avg_fun : film.avg_combined
}

export function Rankings() {
  const [params, setParams] = useSearchParams()
  const sort = parseSort(params.get('sort'))
  const { data, isPending, error } = useRankings(sort)
  const tab = TABS.find((t) => t.sort === sort) ?? TABS[0]

  return (
    <section>
      <h1 className="text-5xl">{tab.label}</h1>
      <p className="mt-2 text-dust">{tab.blurb}</p>

      <div role="tablist" aria-label="Ranking type" className="mt-5 flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t.sort}
            role="tab"
            type="button"
            aria-selected={t.sort === sort}
            onClick={() => setParams({ sort: t.sort }, { replace: true })}
            className={`rounded px-3 py-1.5 text-sm font-semibold ${
              t.sort === sort ? 'bg-blood text-white' : 'bg-shelf text-dust hover:text-bone'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="mt-6">
        {isPending && <Loading />}
        {error && <ErrorText>{errorMessage(error)}</ErrorText>}
        {data && data.length === 0 && (
          <div className="rounded bg-shelf p-6">
            <p className="font-semibold">Nothing ranked yet.</p>
            <p className="mt-1 text-dust">
              Add a film you watched and rate it, and it will show up here.
            </p>
            <Link to="/add" className="btn mt-4">
              Add a film
            </Link>
          </div>
        )}
        {data && data.length > 0 && (
          <ol className="grid grid-cols-[minmax(0,1fr)] gap-2">
            {data.map((film) => (
              <li key={film.id}>
                <Link
                  to={`/films/${film.id}`}
                  className="flex items-center gap-4 rounded bg-shelf p-3 hover:bg-shelf-hi"
                >
                  <span
                    className="w-9 shrink-0 text-right text-3xl font-bold tabular-nums text-blood"
                    aria-label={`Rank ${film.rank}`}
                  >
                    {film.rank}
                  </span>
                  <Poster title={film.title} url={film.poster_url} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-lg font-semibold">
                      {film.title}
                      {film.year ? <span className="font-normal text-dust"> ({film.year})</span> : null}
                    </p>
                    <ul className="mt-1 flex flex-wrap gap-1.5 text-xs">
                      {film.scores.map((s) => (
                        <li
                          key={s.user_id}
                          className="rounded-full bg-tape px-2 py-0.5 text-dust"
                          title={`${s.display_name}: badness ${s.badness}, fun ${s.fun}`}
                        >
                          {s.display_name}{' '}
                          <b className="text-bone">
                            {sort === 'badness'
                              ? s.badness
                              : sort === 'fun'
                                ? s.fun
                                : `${s.badness}/${s.fun}`}
                          </b>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <span
                    className="sticker text-lg"
                    title={`Badness ${formatScore(film.avg_badness)}, fun ${formatScore(film.avg_fun)}`}
                  >
                    {formatScore(mainScore(film, sort))}
                  </span>
                </Link>
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  )
}
