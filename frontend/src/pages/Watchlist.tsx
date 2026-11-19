import { Link, useNavigate } from 'react-router-dom'
import { errorMessage } from '../api/client'
import { useFilms, useMarkWatched } from '../api/queries'
import { ErrorText, Loading, Poster } from '../components/bits'

export function Watchlist() {
  const { data, isPending, error } = useFilms('watchlist')
  const markWatched = useMarkWatched()
  const navigate = useNavigate()

  return (
    <section>
      <h1 className="text-5xl">Watchlist</h1>
      <p className="mt-2 text-dust">Films the club hasn’t sat through yet.</p>

      <div className="mt-6">
        {isPending && <Loading />}
        {error && <ErrorText>{errorMessage(error)}</ErrorText>}
        <ErrorText>{markWatched.isError ? errorMessage(markWatched.error) : null}</ErrorText>
        {data && data.length === 0 && (
          <div className="rounded bg-shelf p-6">
            <p className="font-semibold">The watchlist is empty.</p>
            <p className="mt-1 text-dust">Add the next terrible film you want to try.</p>
            <Link to="/add" className="btn mt-4">
              Add a film
            </Link>
          </div>
        )}
        {data && data.length > 0 && (
          <ul className="grid grid-cols-[minmax(0,1fr)] gap-2">
            {data.map((film) => (
              <li key={film.id} className="flex items-center gap-4 rounded bg-shelf p-3">
                <Poster title={film.title} url={film.poster_url} className="h-16 w-11" />
                <Link to={`/films/${film.id}`} className="min-w-0 flex-1 truncate font-semibold">
                  {film.title}
                  {film.year ? <span className="font-normal text-dust"> ({film.year})</span> : null}
                </Link>
                <button
                  type="button"
                  className="btn text-sm"
                  disabled={markWatched.isPending}
                  onClick={() =>
                    markWatched.mutate(film.id, {
                      onSuccess: () => navigate(`/films/${film.id}`),
                    })
                  }
                >
                  We watched it
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
