import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { errorMessage } from '../api/client'
import { useAddFilm } from '../api/queries'
import { ErrorText } from '../components/bits'

export function AddFilm() {
  const navigate = useNavigate()
  const add = useAddFilm()
  const [title, setTitle] = useState('')
  const [year, setYear] = useState('')
  const [status, setStatus] = useState<'watchlist' | 'watched'>('watched')

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    add.mutate(
      { title, year: year ? Number(year) : null, status },
      {
        onSuccess: (film) => navigate(status === 'watched' ? `/films/${film.id}` : '/watchlist'),
      },
    )
  }

  return (
    <section className="max-w-lg">
      <h1 className="text-5xl">Add a film</h1>
      <form onSubmit={onSubmit} className="mt-6 grid gap-5">
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
