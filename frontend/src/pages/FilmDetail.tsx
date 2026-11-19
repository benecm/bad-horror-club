import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { errorMessage } from '../api/client'
import type { FilmDetail as FilmDetailData, RatingOut } from '../api/client'
import {
  useAddQuote,
  useDeleteFilm,
  useDeleteQuote,
  useDeleteRating,
  useFilm,
  useMarkWatched,
  useSaveRating,
} from '../api/queries'
import { useAuth } from '../auth'
import { ErrorText, Loading, Poster } from '../components/bits'

export function FilmDetail() {
  const { id } = useParams()
  const filmId = Number(id)
  const { data: film, isPending, error } = useFilm(filmId)

  if (isPending) return <Loading />
  if (error || !film) {
    return (
      <div className="grid gap-3">
        <ErrorText>{errorMessage(error)}</ErrorText>
        <Link to="/" className="underline">
          Back to the rankings
        </Link>
      </div>
    )
  }
  return <FilmView film={film} />
}

function FilmView({ film }: { film: FilmDetailData }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const markWatched = useMarkWatched()
  const deleteFilm = useDeleteFilm()
  const mine = film.ratings.find((r) => r.user.id === user?.id)
  const watched = film.status === 'watched'

  return (
    <article className="grid grid-cols-[minmax(0,1fr)] gap-8">
      <header className="flex gap-4">
        <Poster title={film.title} url={film.poster_url} className="h-40 w-28" />
        <div className="min-w-0">
          <h1 className="text-4xl sm:text-5xl">{film.title}</h1>
          <p className="mt-2 text-dust">
            {film.year ? `${film.year} · ` : ''}
            {watched
              ? `Watched${film.watched_on ? ` on ${film.watched_on}` : ''}`
              : 'On the watchlist'}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {!watched && (
              <button
                type="button"
                className="btn"
                disabled={markWatched.isPending}
                onClick={() => markWatched.mutate(film.id)}
              >
                We watched it
              </button>
            )}
            {film.added_by === user?.id && (
              <button
                type="button"
                className="btn btn-quiet"
                disabled={deleteFilm.isPending}
                onClick={() => {
                  if (window.confirm(`Delete “${film.title}” and all its ratings?`)) {
                    deleteFilm.mutate(film.id, { onSuccess: () => navigate('/') })
                  }
                }}
              >
                Delete film
              </button>
            )}
          </div>
          <div className="mt-3 grid gap-2">
            <ErrorText>{markWatched.isError ? errorMessage(markWatched.error) : null}</ErrorText>
            <ErrorText>{deleteFilm.isError ? errorMessage(deleteFilm.error) : null}</ErrorText>
          </div>
        </div>
      </header>

      {watched ? (
        <RatingForm key={mine ? `${mine.id}-${mine.updated_at}` : 'new'} film={film} mine={mine} />
      ) : (
        <p className="rounded bg-shelf p-4 text-dust">
          Once the club has watched it, mark it as watched and everyone can rate it.
        </p>
      )}

      <section>
        <h2 className="text-3xl">What the club thinks</h2>
        {film.ratings.length === 0 ? (
          <p className="mt-3 text-dust">No ratings yet.</p>
        ) : (
          <ul className="mt-4 grid grid-cols-[minmax(0,1fr)] gap-3">
            {film.ratings.map((r) => (
              <li key={r.id} className="rounded bg-shelf p-4">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <p className="font-semibold">{r.user.display_name}</p>
                  <p className="text-sm text-dust">
                    Badness <b className="text-bone">{r.badness}</b> · Fun{' '}
                    <b className="text-bone">{r.fun}</b>
                  </p>
                </div>
                {r.comment && <p className="mt-2 whitespace-pre-wrap">{r.comment}</p>}
              </li>
            ))}
          </ul>
        )}
      </section>

      {watched && <Quotes film={film} />}
    </article>
  )
}

function Quotes({ film }: { film: FilmDetailData }) {
  const { user } = useAuth()
  const add = useAddQuote(film.id)
  const remove = useDeleteQuote()
  const [text, setText] = useState('')

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    add.mutate(text, { onSuccess: () => setText('') })
  }

  return (
    <section>
      <h2 className="text-3xl">Best lines</h2>
      {film.quotes.length === 0 ? (
        <p className="mt-3 text-dust">No quotes yet. What did somebody say that you can’t forget?</p>
      ) : (
        <ul className="mt-4 grid grid-cols-[minmax(0,1fr)] gap-3">
          {film.quotes.map((q) => (
            <li key={q.id} className="rounded bg-shelf p-4">
              <blockquote className="whitespace-pre-wrap text-lg">“{q.text}”</blockquote>
              <div className="mt-2 flex items-center justify-between text-sm text-dust">
                <span>Added by {q.user.display_name}</span>
                {q.user.id === user?.id && (
                  <button
                    type="button"
                    className="underline hover:text-bone"
                    disabled={remove.isPending}
                    onClick={() => remove.mutate(q.id)}
                  >
                    Delete
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={onSubmit} className="mt-4 grid gap-2">
        <label className="grid gap-1">
          <span className="text-sm text-dust">Add a quote</span>
          <textarea
            className="field min-h-16"
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={500}
            required
          />
        </label>
        <ErrorText>
          {add.isError ? errorMessage(add.error) : remove.isError ? errorMessage(remove.error) : null}
        </ErrorText>
        <div>
          <button type="submit" className="btn" disabled={add.isPending || !text.trim()}>
            {add.isPending ? 'Adding…' : 'Add quote'}
          </button>
        </div>
      </form>
    </section>
  )
}

function Slider({
  label,
  hint,
  value,
  onChange,
}: {
  label: string
  hint: string
  value: number
  onChange: (n: number) => void
}) {
  return (
    <label className="grid gap-2">
      <span className="flex items-baseline justify-between">
        <span className="font-semibold">
          {label} <span className="font-normal text-dust">{hint}</span>
        </span>
        <span className="sticker text-lg">{value}</span>
      </span>
      <input
        type="range"
        min={1}
        max={10}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  )
}

function RatingForm({ film, mine }: { film: FilmDetailData; mine: RatingOut | undefined }) {
  const [badness, setBadness] = useState(mine?.badness ?? 5)
  const [fun, setFun] = useState(mine?.fun ?? 5)
  const [comment, setComment] = useState(mine?.comment ?? '')
  const save = useSaveRating(film.id)
  const remove = useDeleteRating(film.id)

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    save.mutate({ badness, fun, comment: comment.trim() || null })
  }

  return (
    <form onSubmit={onSubmit} className="grid gap-5 rounded bg-shelf p-5">
      <h2 className="text-3xl">{mine ? 'Your rating' : 'Rate it'}</h2>
      <Slider
        label="Badness"
        hint="1 is almost decent, 10 is a disaster"
        value={badness}
        onChange={setBadness}
      />
      <Slider
        label="Fun"
        hint="1 was a slog, 10 was a riot"
        value={fun}
        onChange={setFun}
      />
      <label className="grid gap-1">
        <span className="text-sm text-dust">Comment (optional)</span>
        <textarea
          className="field min-h-24"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          maxLength={2000}
        />
      </label>
      <ErrorText>
        {save.isError
          ? errorMessage(save.error)
          : remove.isError
            ? errorMessage(remove.error)
            : null}
      </ErrorText>
      <div className="flex flex-wrap items-center gap-3">
        <button type="submit" className="btn" disabled={save.isPending}>
          {save.isPending ? 'Saving…' : mine ? 'Update rating' : 'Save rating'}
        </button>
        {mine && (
          <button
            type="button"
            className="btn btn-quiet"
            disabled={remove.isPending}
            onClick={() => remove.mutate()}
          >
            Remove my rating
          </button>
        )}
        {save.isSuccess && !save.isPending && <span className="text-sm text-dust">Saved.</span>}
      </div>
    </form>
  )
}
