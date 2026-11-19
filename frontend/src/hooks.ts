import { useEffect, useState } from 'react'

/** Returns `value`, but only after it has stopped changing for `delayMs`. */
export function useDebounced<T>(value: T, delayMs = 350): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = window.setTimeout(() => setDebounced(value), delayMs)
    return () => window.clearTimeout(t)
  }, [value, delayMs])
  return debounced
}
