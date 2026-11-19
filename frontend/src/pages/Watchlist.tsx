import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { errorMessage } from '../api/client'
import type { FilmOut } from '../api/client'
import { useFilms, useMarkWatched, useVote } from '../api/queries'
import { useAuth } from '../auth'
import { ErrorText, Loading, Poster } from '../components/bits'

/** Random pick among the most-voted films, or among all of them if nobody has voted. */
function pickTonight(films: FilmOut[]): FilmOut | undefined {
  const top = Math.max(...films.map((f) => f.vote_user_ids.length))
  const pool = top > 0 ? films.filter((f) => f.vote_user_ids.length === top) : films
  return pool[Math.floor(Math.random() * pool.length)]
}

export function Watchlist() {
  const { user } = useAuth()
  const { data, isPending, error } = useFilms('watchlist')
  const markWatched = useMarkWatched()
  const vote = useVote()
  const navigate = useNavigate()
  const [pickedId, setPickedId] = useState<number | null>(null)

  const films = data
    ? [...data].sort(
        (a, b) =>
          b.vote_user_ids.length - a.vote_user_ids.length ||
          a.created_at.localeCompare(b.created_at),
      )
    : []
  const picked = films.find((f) => f.id === pickedId)

  function watched(film: FilmOut) {
    markWatched.mutate(film.id, { onSuccess: () => navigate(`/films/${film.id}`) })
  }

  return (
    <section>
      <h1 className="text-5xl">Watchlist</h1>
      <p className="mt-2 text-dust">
        Films the club hasn’t sat through yet. Vote for what to watch next.
      </p>

      <div className="mt-6 grid grid-cols-[minmax(0,1fr)] gap-3">
        {isPending && <Loading />}
        {error && <ErrorText>{errorMessage(error)}</ErrorText>}
        <ErrorText>{markWatched.isError ? errorMessage(markWatched.error) : null}</ErrorText>
        <ErrorText>{vote.isError ? errorMessage(vote.error) : null}</ErrorText>

        {data && data.length === 0 && (
          <div className="rounded bg-shelf p-6">
            <p className="font-semibold">The watchlist is empty.</p>
            <p className="mt-1 text-dust">Add the next terrible film you want to try.</p>
            <Link to="/add" className="btn mt-4">
              Add a film
            </Link>
          </div>
        )}

        {films.length > 0 && (
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              className="btn"
              onClick={() => setPickedId(pickTonight(films)?.id ?? null)}
            >
              {picked ? 'Pick again' : 'Pick tonight’s film'}
            </button>
            <span className="text-sm text-dust">
              Chosen at random from the most voted, or from everything if nobody has voted.
            </span>
          </div>
        )}

        {picked && (
          <div
            role="status"
            className="flex items-center gap-4 rounded bg-blood-dim/30 p-4 ring-1 ring-blood"
          >
            <Poster title={picked.title} url={picked.poster_url} className="h-24 w-16" />
            <div className="min-w-0 flex-1">
              <p className="text-sm text-dust">Tonight’s film</p>
              <p className="truncate font-display text-3xl">{picked.title}</p>
            </div>
            <button
              type="button"
              className="btn"
              disabled={markWatched.isPending}
              onClick={() => watched(picked)}
            >
              We watched it
            </button>
          </div>
        )}

        {films.length > 0 && (
          <ul className="grid grid-cols-[minmax(0,1fr)] gap-2">
            {films.map((film) => {
              const voted = user ? film.vote_user_ids.includes(user.id) : false
              const count = film.vote_user_ids.length
              return (
                <li
                  key={film.id}
                  className={`flex items-center gap-3 rounded bg-shelf p-3 ${
                    film.id === pickedId ? 'ring-1 ring-blood' : ''
                  }`}
                >
                  <Poster title={film.title} url={film.poster_url} className="h-16 w-11" />
                  <Link to={`/films/${film.id}`} className="min-w-0 flex-1 truncate font-semibold">
                    {film.title}
                    {film.year ? (
                      <span className="font-normal text-dust"> ({film.year})</span>
                    ) : null}
                  </Link>
                  <button
                    type="button"
                    aria-pressed={voted}
                    disabled={vote.isPending}
                    onClick={() => vote.mutate({ id: film.id, vote: !voted })}
                    className={`btn text-sm ${voted ? '' : 'btn-quiet'}`}
                    title={voted ? 'Take back your vote' : 'Vote to watch this next'}
                  >
                    {voted ? 'Voted' : 'Vote'} · {count}
                  </button>
                  <button
                    type="button"
                    className="btn btn-quiet text-sm"
                    disabled={markWatched.isPending}
                    onClick={() => watched(film)}
                  >
                    We watched it
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </section>
  )
}
