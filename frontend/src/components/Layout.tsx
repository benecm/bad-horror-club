import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded px-3 py-1.5 font-medium ${
    isActive ? 'bg-shelf-hi text-bone' : 'text-dust hover:text-bone'
  }`

export function Layout() {
  const { user, signOut } = useAuth()
  return (
    <div className="mx-auto min-h-dvh max-w-3xl px-4 pb-16">
      <header className="flex flex-wrap items-center justify-between gap-3 py-5">
        <NavLink to="/" className="font-display text-3xl text-blood">
          Bad Horror Club
        </NavLink>
        <nav className="flex flex-wrap items-center gap-1 text-sm">
          <NavLink to="/" end className={linkClass}>
            Rankings
          </NavLink>
          <NavLink to="/watchlist" className={linkClass}>
            Watchlist
          </NavLink>
          <NavLink to="/bottom250" className={linkClass}>
            Bottom 250
          </NavLink>
          <NavLink to="/stats" className={linkClass}>
            Stats
          </NavLink>
          <NavLink to="/add" className="btn ml-1 !py-1.5 text-sm">
            Add film
          </NavLink>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
      <footer className="mt-12 flex items-center justify-between text-sm text-dust">
        <span>Signed in as {user?.display_name}</span>
        <button type="button" onClick={signOut} className="underline hover:text-bone">
          Sign out
        </button>
      </footer>
    </div>
  )
}
