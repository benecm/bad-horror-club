export function Poster({
  title,
  url,
  className = 'h-24 w-16',
}: {
  title: string
  url?: string | null
  className?: string
}) {
  if (url) {
    return <img src={url} alt="" loading="lazy" className={`${className} shrink-0 rounded object-cover`} />
  }
  return (
    <div
      aria-hidden
      className={`${className} grid shrink-0 place-items-center rounded bg-shelf-hi font-display text-2xl text-blood-dim`}
    >
      {title.trim().charAt(0).toUpperCase()}
    </div>
  )
}

export function ErrorText({ children }: { children: string | null | undefined }) {
  if (!children) return null
  return (
    <p role="alert" className="rounded bg-blood-dim/25 px-3 py-2 text-sm text-bone">
      {children}
    </p>
  )
}

export function Loading({ what = 'the tapes' }: { what?: string }) {
  return <p className="py-10 text-dust">Rewinding {what}…</p>
}

export function formatScore(n: number): string {
  return Number.isInteger(n) ? n.toFixed(1) : String(n)
}
