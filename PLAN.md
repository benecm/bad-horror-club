# Bad Horror Club: build and hosting plan

A small website where a group of friends logs the bad horror films they watch, rates each one, and sees a ranking from worst to "best".

This file is written so you can put it in the repo root and tell Claude Code: *"Read PLAN.md and do Phase 1."* Work phase by phase. Check that each phase runs before starting the next.

---

## 1. Stack

| Part | Choice | Why |
|---|---|---|
| Backend | Python 3.12, **FastAPI**, SQLAlchemy 2.0, Alembic, Pydantic v2 | Modern, typed, and the API docs are generated for you at `/docs` |
| Python tooling | **uv** (dependencies and virtual env), ruff (lint), pytest | Fast and simple |
| Database | **PostgreSQL**: Docker locally, **Neon** in production | Neon's free tier doesn't expire, so the data stays |
| Auth | Username + password, argon2 hashing (`pwdlib`), JWT (`PyJWT`) in the `Authorization` header | No cross-domain cookie problems |
| Frontend | **React + TypeScript + Vite**, React Router, TanStack Query | Clean data fetching and caching |
| Styling | Tailwind CSS | Quick to build a dark, horror-themed look |
| API types | `openapi-typescript`, which generates TS types from FastAPI's OpenAPI schema | Frontend and backend types can't drift apart |
| Film info (optional) | TMDB API (free key) | Posters, year and description from the title |

---

## 2. Repo structure

```
bad-horror-club/
├── PLAN.md
├── CLAUDE.md              # short rules for Claude Code (see section 9)
├── docker-compose.yml     # local Postgres only
├── render.yaml            # Render blueprint (backend + frontend)
├── .github/workflows/
│   ├── ci.yml             # lint + tests on every push
│   └── backup.yml         # weekly database backup
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/
│   ├── app/
│   │   ├── main.py        # FastAPI app, CORS, routers
│   │   ├── config.py      # pydantic-settings, reads env vars
│   │   ├── db.py          # engine + session dependency
│   │   ├── models.py      # SQLAlchemy models
│   │   ├── schemas.py     # Pydantic request/response models
│   │   ├── auth.py        # hashing, JWT, get_current_user
│   │   └── routers/
│   │       ├── auth.py
│   │       ├── films.py
│   │       ├── ratings.py
│   │       └── rankings.py
│   └── tests/
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── .env.example       # VITE_API_URL=http://localhost:8000
    └── src/
        ├── api/           # fetch client + generated types
        ├── pages/         # Login, Rankings, FilmDetail, AddFilm, Watchlist
        ├── components/
        └── main.tsx
```

---

## 3. Data model

**users**
- `id` (PK), `username` (unique), `display_name`, `password_hash`, `created_at`

**films**
- `id` (PK), `title`, `year` (nullable), `poster_url` (nullable), `tmdb_id` (nullable, unique)
- `status`: `watchlist` | `watched`
- `watched_on` (date, nullable)
- `added_by` (FK users), `created_at`

**ratings**
- `id` (PK), `film_id` (FK films, cascade delete), `user_id` (FK users)
- `badness` (int 1–10): how terrible the film is
- `fun` (int 1–10): how much you enjoyed watching it
- `comment` (text, nullable), `created_at`, `updated_at`
- **Unique (`film_id`, `user_id`)**: one rating per person per film; rating again updates it

**quotes** (Phase 5, optional)
- `id`, `film_id`, `user_id`, `text`, `created_at`. Holds the best lines from the movie night.

Rankings aren't stored. They're computed with SQL (`AVG(badness)`, `AVG(fun)`, `COUNT(ratings)`) so they're never out of date.

---

## 4. API

All routes are under `/api`. Everything except `register`, `login` and `health` needs a valid JWT.

| Method | Path | What it does |
|---|---|---|
| GET | `/api/health` | Returns `{"ok": true}`. Used by Render and the frontend's wake-up check |
| POST | `/api/auth/register` | `{username, display_name, password, join_code}`. Only works with the correct `JOIN_CODE`, so strangers can't sign up |
| POST | `/api/auth/login` | Returns `{access_token}` |
| GET | `/api/auth/me` | Current user |
| GET | `/api/films?status=watched` | List of films |
| POST | `/api/films` | Add a film (to the watchlist or as watched) |
| GET | `/api/films/{id}` | Film plus every rating and comment |
| PATCH | `/api/films/{id}` | Edit, or mark as watched |
| DELETE | `/api/films/{id}` | Only the person who added it |
| PUT | `/api/films/{id}/rating` | Create or update *my* rating `{badness, fun, comment}` |
| DELETE | `/api/films/{id}/rating` | Remove my rating |
| GET | `/api/rankings?sort=badness\|fun\|combined` | Watched films with averages, sorted, ranked 1…n |
| GET | `/api/stats` | Films watched, harshest critic, most generous critic, and so on |
| GET | `/api/export` | Full JSON dump of everything (an extra backup) |
| GET | `/api/tmdb/search?q=` | (optional) Proxies TMDB so the API key stays on the server |

`combined` = `(badness + fun) / 2`, which gives a "so bad it's good" score.

---

## 5. Frontend pages

- **Login / Register**: register asks for the club's join code
- **Rankings** (home): tabs for *Hall of shame* (badness), *So bad it's good* (fun) and *Combined*. Each row shows rank, poster, title, year, average score, and every friend's score as small chips
- **Film detail**: poster, everyone's ratings and comments, and my own rating form (two 1–10 sliders and a comment)
- **Add film**: type a title, optionally pick a TMDB match, choose *Watchlist* or *Watched tonight*
- **Watchlist**: films you haven't watched yet, with a "We watched it" button
- **Stats**: small summary cards

**Important UX detail:** the free backend sleeps when nobody uses it (see section 7). On app load, call `/api/health` and show a friendly "Waking up the crypt… (up to a minute)" screen until it responds.

Theme: dark background, red accent, a creepy display font for headings only (for example *Creepster* from Google Fonts), normal readable font for everything else.

---

## 6. Build phases (one Claude Code session per phase)

**Phase 1: Backend skeleton**
- uv project, FastAPI app, config via env vars, `/api/health`
- `docker-compose.yml` with Postgres 16
- SQLAlchemy models + first Alembic migration
- pytest setup with a test database
- ✅ Done when `uv run uvicorn app.main:app --reload` works and `/docs` loads

**Phase 2: Auth + films + ratings**
- Register (with join code), login, `me`
- Films CRUD, rating upsert, validation (1–10)
- Tests for each endpoint, including "can't rate twice" and "wrong join code"
- ✅ Done when the tests pass and you can do the whole flow from `/docs`

**Phase 3: Rankings, stats, export**
- SQL aggregate queries, the three sort modes, ties handled consistently
- `/api/export`
- ✅ Done when tests with seeded data return the correct order

**Phase 4: Frontend**
- Vite React TS app, Tailwind, router, TanStack Query
- Generate types: `npx openapi-typescript http://localhost:8000/openapi.json -o src/api/schema.d.ts`
- All pages from section 5, the wake-up screen, token stored in localStorage
- ✅ Done when you can register, add a film, rate it and see it ranked, all running locally

**Phase 5: Deploy + backups** (section 7 and 8)

**Phase 6: Extras (optional)**
- TMDB search and posters, quotes, a "pick tonight's film" random button from the watchlist, a vote on the next film

---

## 7. Hosting (free, with permanent data)

The key idea is to **keep the data away from the app server.** Render's free servers can restart at any time and lose their local files, so the database lives on Neon instead.

### Database: Neon (free, no expiry)
- Neon's free plan has no time limit. It gives each project 100 compute hours a month and at least 0.5 GB of storage, which is far more than a film list needs.
- It scales to zero after about 5 minutes idle and wakes up automatically on the next query.
- Steps:
  1. Sign up at neon.com (no credit card needed) and create a project, region **Frankfurt (eu-central-1)**
  2. Copy the **pooled** connection string
  3. Change its prefix to `postgresql+psycopg://` for SQLAlchemy and keep `?sslmode=require`

> Why not Supabase or Render Postgres? Render's free Postgres is deleted after 30 days. Supabase's free projects pause after a week without activity, and you have to resume them by hand.

### Backend: Render free web service
- Spins down after 15 minutes without traffic, and the first request after that takes about a minute. That's fine for a movie-night site, and the wake-up screen covers it.
- Settings (put these in `render.yaml`):
  - Root dir: `backend`
  - Build: `pip install uv && uv sync --frozen`
  - Start: `uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
    (runs migrations on every start, so you don't need Render's paid pre-deploy step)
  - Health check path: `/api/health`
  - Region: **Frankfurt** (same region as Neon, so queries are fast)
- Environment variables:
  - `DATABASE_URL` (from Neon)
  - `JWT_SECRET` (long random string)
  - `JOIN_CODE` (the secret word you give your friends)
  - `CORS_ORIGINS` (the frontend URL, e.g. `https://bad-horror-club.onrender.com`)
  - `PYTHON_VERSION=3.12.7`
  - `TMDB_API_KEY` (optional)

### Frontend: Render static site (free, doesn't sleep)
- Root dir: `frontend`
- Build: `npm ci && npm run build`
- Publish dir: `dist`
- Env var: `VITE_API_URL=https://<your-backend>.onrender.com`
- Add a rewrite rule `/*` → `/index.html` so React Router routes work on refresh
- Alternatives that work just as well: Cloudflare Pages, Netlify, GitHub Pages

### Deploy flow
Push to GitHub → Render auto-deploys both services from `render.yaml` (Blueprint).

---

## 8. Backups (so you never lose the list)

Three layers, from most to least important:

1. **Weekly automatic dump via GitHub Actions** (`.github/workflows/backup.yml`)
   - Runs on a schedule (e.g. every Sunday) and can also be run by hand
   - Installs the Postgres client, runs `pg_dump "$DATABASE_URL" > backup.sql`
   - Uploads it as a workflow artifact (keeps 90 days), **or** commits it to a separate **private** repo for a permanent history
   - `DATABASE_URL` goes in GitHub repo secrets (use the plain `postgresql://` form for `pg_dump`)
2. **In-app export**: an "Export everything" button that downloads `/api/export` as JSON
3. **Neon's built-in restore**: the free plan lets you roll back a few hours, which helps after an accidental delete

Restore test: once, after setting this up, load a backup into your local Docker Postgres with `psql` to make sure it actually works.

---

## 9. CLAUDE.md (put this in the repo root)

```markdown
# Project rules
- Backend: FastAPI + SQLAlchemy 2.0 (typed `Mapped[]` style) + Alembic. Use uv, never pip directly.
- Every schema change = a new Alembic migration. Never edit old migrations.
- Every new endpoint gets a pytest test.
- Frontend: React + TS strict mode, TanStack Query for all server data, no `any`.
- Regenerate API types after backend changes: `npm run gen:api` in frontend/.
- Secrets only via env vars; never commit .env files.
- Run `uv run ruff check . && uv run pytest` (backend) and `npm run build` (frontend) before saying a task is done.
```

---

## 10. Local development cheat sheet

```bash
# database
docker compose up -d

# backend
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload     # http://localhost:8000/docs

# frontend
cd frontend
npm install
npm run dev                               # http://localhost:5173
```

---

## 11. Cost summary

| Service | Plan | Cost |
|---|---|---|
| Neon (database) | Free | €0, no expiry |
| Render backend | Free web service | €0, sleeps when idle |
| Render frontend | Free static site | €0 |
| GitHub (code, CI, backups) | Free | €0 |
| **Total** | | **€0** |

If the sleep ever gets annoying, Render's smallest always-on instance costs about $7/month. That's the only upgrade you'd likely want, and the data doesn't need to move.
