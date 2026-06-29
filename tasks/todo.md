# Deployment Todo

## Phase 1: Code Changes (Claude does these)
- [ ] Task 1: Update CORS to use `ALLOWED_ORIGINS` env var
- [ ] Task 2: Multi-stage Dockerfile to bundle React into FastAPI static/
- [ ] Task 3: Add `railway.toml` with backend + celery-worker services
- [ ] Task 4: Fix alembic to read `DATABASE_URL` from env

## Checkpoint 1
- [ ] Docker build succeeds locally
- [ ] SPA served by FastAPI at port 8000
- [ ] Code pushed to GitHub

## Phase 2: Railway Setup (You do these)
- [ ] Task 5: Create Railway project + PostgreSQL + Redis plugins
- [ ] Task 6: Run `alembic upgrade head` against Railway DB
- [ ] Task 7: Deploy both services, set env vars

## Checkpoint 2
- [ ] CRM live at *.up.railway.app
- [ ] Login works
- [ ] Uploads work

## Phase 3: Optional
- [ ] Task 8: Custom domain `crm.ntcplai.com`
