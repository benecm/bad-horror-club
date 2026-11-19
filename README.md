# Bad Horror Club

A small site where friends log the bad horror films they watch, rate them, and rank them from worst to "best".
See `PLAN.md` for the design and `CLAUDE.md` for project rules.

## Local development

```bash
docker compose up -d                      # Postgres 17 (same major version as Neon)

cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload      # http://localhost:8000/docs

cd frontend
npm install
npm run dev                               # http://localhost:5173
```

Backend checks: `uv run ruff check . && uv run pytest`. Frontend: `npm run build`.
After changing the API, regenerate types with the backend running: `npm run gen:api`.

## Bottom 250

The Bottom 250 page lists Letterboxd's "bottom 250 horror films" and rolls a random number to pick one.
The app reads a snapshot (`backend/app/data/bottom250.json`) and never calls Letterboxd while running.
The list changes every week; to refresh the snapshot, run `uv run python scripts/update_bottom250.py`
in `backend/` and commit the result.

## Hosting

Neon (database) + Render free web service (backend) + Render static site (frontend), all defined in
`render.yaml`. Secrets (`DATABASE_URL`, `JOIN_CODE`) are set in the Render dashboard, never in git.

## Backups and restore

A GitHub Action (`backup.yml`) dumps the Neon database every Sunday and uploads it as a workflow artifact
for 90 days. The repo is public and anyone signed in to GitHub can download artifacts, so **the dump is
encrypted** with the public key in `.github/backup-public-key.asc`. The private key is not in this repo.

To restore:

```bash
gh run download <run-id> -n database-backup
gpg --decrypt backup-YYYY-MM-DD.sql.gz.gpg | gunzip > backup.sql   # needs the private key
createdb restore_test
psql -d restore_test -v ON_ERROR_STOP=1 -f backup.sql              # Postgres 17 or newer
```

You can also download a JSON copy from the Stats page ("Export everything").
