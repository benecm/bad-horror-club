import { useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api, errorMessage, unwrap } from '../api/client'
import type { StatsOut } from '../api/client'
import { useStats } from '../api/queries'
import { ErrorText, Loading, formatScore } from '../components/bits'

function Fact({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded bg-shelf p-4">
      <p className="text-sm text-dust">{title}</p>
      <div className="mt-1 text-xl font-semibold">{children}</div>
    </div>
  )
}

function Critic({ c }: { c: NonNullable<StatsOut['harshest_critic']> }) {
  return (
    <>
      {c.display_name}
      <span className="block text-sm font-normal text-dust">
        average badness {formatScore(c.avg_badness)} over {c.rating_count}{' '}
        {c.rating_count === 1 ? 'film' : 'films'}
      </span>
    </>
  )
}

export function Stats() {
  const { data, isPending, error } = useStats()

  const exportAll = useMutation({
    mutationFn: async () => {
      const dump = await unwrap(api.GET('/api/export'))
      const blob = new Blob([JSON.stringify(dump, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `bad-horror-club-${new Date().toISOString().slice(0, 10)}.json`
      a.click()
      URL.revokeObjectURL(url)
    },
  })

  return (
    <section>
      <h1 className="text-5xl">Stats</h1>

      <div className="mt-6">
        {isPending && <Loading what="the numbers" />}
        {error && <ErrorText>{errorMessage(error)}</ErrorText>}
        {data && (
          <div className="grid gap-3 sm:grid-cols-2">
            <Fact title="Films watched">{data.films_watched}</Fact>
            <Fact title="Still on the watchlist">{data.films_on_watchlist}</Fact>
            <Fact title="Ratings given">
              {data.total_ratings} from {data.members} {data.members === 1 ? 'member' : 'members'}
            </Fact>
            <Fact title="Worst film so far">
              {data.worst_film ? (
                <Link to={`/films/${data.worst_film.id}`} className="underline">
                  {data.worst_film.title}
                  <span className="block text-sm font-normal text-dust">
                    badness {formatScore(data.worst_film.score)}
                  </span>
                </Link>
              ) : (
                <span className="text-dust">No ratings yet</span>
              )}
            </Fact>
            <Fact title="Most fun film">
              {data.most_fun_film ? (
                <Link to={`/films/${data.most_fun_film.id}`} className="underline">
                  {data.most_fun_film.title}
                  <span className="block text-sm font-normal text-dust">
                    fun {formatScore(data.most_fun_film.score)}
                  </span>
                </Link>
              ) : (
                <span className="text-dust">No ratings yet</span>
              )}
            </Fact>
            <Fact title="Harshest critic">
              {data.harshest_critic ? (
                <Critic c={data.harshest_critic} />
              ) : (
                <span className="text-dust">No ratings yet</span>
              )}
            </Fact>
            <Fact title="Most generous critic">
              {data.most_generous_critic ? (
                <Critic c={data.most_generous_critic} />
              ) : (
                <span className="text-dust">No ratings yet</span>
              )}
            </Fact>
          </div>
        )}
      </div>

      <div className="mt-10 grid max-w-md gap-2">
        <h2 className="text-3xl">Back it up</h2>
        <p className="text-dust">Download every film, rating and member as a JSON file.</p>
        <ErrorText>{exportAll.isError ? errorMessage(exportAll.error) : null}</ErrorText>
        <div>
          <button
            type="button"
            className="btn btn-quiet"
            disabled={exportAll.isPending}
            onClick={() => exportAll.mutate()}
          >
            {exportAll.isPending ? 'Preparing…' : 'Export everything'}
          </button>
        </div>
      </div>
    </section>
  )
}
