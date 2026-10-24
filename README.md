# LinkSnap

A production-style URL shortener built with FastAPI, PostgreSQL, SQLAlchemy, and a hand-written LRU cache.

**Live demo:** _add after Render deploy_  
**GitHub:** _add after repo is created_

---

## What it does

`POST /links` creates a short code (`aB3xK9`).  
`GET /{short_code}` resolves and redirects — this is the hot path.  
Every redirect atomically inserts a click row and increments the counter in one transaction.  
A hand-written LRU cache sits in front of the DB lookup so repeated hits skip the database.

---

## Quick start (SQLite — zero setup)

```bash
git clone <repo>
cd linksnap
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

---

## Docker (API + Postgres)

```bash
make up        # docker compose up --build -d
make migrate   # alembic upgrade head inside the container
make test      # pytest
make down
```

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | — | Create account |
| POST | `/auth/login` | — | Get JWT |
| POST | `/links` | Bearer | Create short link |
| GET | `/{short_code}` | — | Redirect (key endpoint) |
| GET | `/links/{id}/stats` | Bearer (owner) | Click count + recent clicks |

---

## Index measurement — `short_code` lookup on 100k rows

Benchmark run against SQLite with 100 000 links and 500 lookups:

| | Time (500 lookups) | Per lookup |
|---|---|---|
| **With** UNIQUE index on `short_code` | 266 ms | 0.53 ms |
| **Without** index (seq scan) | 13 669 ms | 27.3 ms |
| **Speedup** | **51×** | |

> On Postgres, run `make measure` to get the full `EXPLAIN ANALYZE` plan.

The `UNIQUE` constraint on `links.short_code` automatically creates a B-tree index, so the speedup is zero-config — it comes for free from the schema design.

---

## LRU cache — hit rate

Hand-written O(1) LRU (hash map + doubly linked list, no `functools.lru_cache`).  
Load test: 1 000 links, 10 "hot" codes, 95 % traffic skewed to hot codes, 3 000 requests.

| | Value |
|---|---|
| Cache hits | 2 866 / 3 000 |
| **Cache hit rate** | **95.5 %** |
| Throughput | ~51 req/s (single-process, SQLite) |

The skewed distribution mirrors real marketing traffic (a few viral links get most clicks).

---

## Project layout

```
app/
├── main.py
├── config.py           settings via pydantic-settings
├── database.py         SQLAlchemy engine + session factory
├── models.py           users, links, clicks
├── schemas.py          Pydantic v2 request/response models
├── routes/
│   ├── auth.py         POST /auth/register, /auth/login
│   ├── links.py        POST /links, GET /links/{id}/stats
│   └── redirect.py     GET /{short_code}  ← key endpoint
├── services/
│   ├── auth.py         JWT issue/verify, passlib hashing
│   └── shortcode.py    base62 generator with collision retry
└── cache/
    └── lru.py          O(1) LRU cache
alembic/                migrations
tests/                  18 pytest tests
scripts/
├── seed.py             seed 100k links + EXPLAIN ANALYZE (Postgres)
└── loadtest.py         skewed redirect load test
```

---

## Tech stack

| Layer | Tool |
|---|---|
| API | Python 3.13, FastAPI |
| Auth | PyJWT, passlib (pbkdf2_sha256) |
| Database | PostgreSQL, SQLAlchemy 2, Alembic |
| Cache | Hand-written LRU (dict + doubly linked list) |
| Testing | pytest, HTTPX / TestClient |
| Containers | Docker, docker-compose |
| Build | Makefile |
| CI/CD | GitHub Actions |
| Deploy | Render (Docker) |

---

## Make targets

```
make install    install dev deps
make run        uvicorn --reload (SQLite)
make test       pytest
make up         docker compose up --build
make down       docker compose down
make migrate    alembic upgrade head (in container)
make measure    seed 100k links + EXPLAIN ANALYZE (Postgres)
make loadtest   skewed redirect load test against localhost:8000
```

---

## Design notes

**Atomic click recording** — `record_click()` inserts a click row and increments
`click_count` inside a single transaction. If either step fails the whole
transaction rolls back, so the counter and click log never drift apart.
`test_transaction.py` forces the counter step to fail and asserts the click row
was rolled back.

**LRU cache** — The redirect handler caches `(link_id, original_url)` keyed by
`short_code`. A cache hit skips the DB read entirely; the click write still
happens on every request. The `X-Cache: HIT / MISS` response header lets you
verify in `curl`.

**Base62 short codes** — 7 characters from `[a-zA-Z0-9]` give 62⁷ ≈ 3.5 trillion
combinations. Collision probability is negligible; we retry up to 10 times anyway.
