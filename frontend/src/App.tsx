import { Navigate, Route, Routes } from 'react-router-dom'
import { RequireAuth } from './auth'
import { Layout } from './components/Layout'
import { AddFilm } from './pages/AddFilm'
import { Bottom250 } from './pages/Bottom250'
import { FilmDetail } from './pages/FilmDetail'
import { Login } from './pages/Login'
import { Rankings } from './pages/Rankings'
import { Stats } from './pages/Stats'
import { Watchlist } from './pages/Watchlist'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Rankings />} />
        <Route path="films/:id" element={<FilmDetail />} />
        <Route path="add" element={<AddFilm />} />
        <Route path="watchlist" element={<Watchlist />} />
        <Route path="bottom250" element={<Bottom250 />} />
        <Route path="stats" element={<Stats />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
