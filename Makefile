.PHONY: help install dev run test up down logs migrate measure loadtest clean

help:
	@echo "LinkSnap Makefile targets:"
	@echo "  make install   install dev dependencies (SQLite local dev)"
	@echo "  make run        run the API with reload (SQLite)"
	@echo "  make test       run pytest (SQLite)"
	@echo "  make up         build + start API + Postgres via Docker"
	@echo "  make down       stop Docker stack"
	@echo "  make logs       tail API logs"
	@echo "  make migrate    run Alembic migrations against the Docker DB"
	@echo "  make measure    seed 100k links + EXPLAIN ANALYZE (Docker DB)"
	@echo "  make loadtest   skewed load test against localhost:8000"
	@echo "  make clean      remove local SQLite db files"

install:
	pip install -r requirements-dev.txt

run:
	uvicorn app.main:app --reload

test:
	pytest -v

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f api

migrate:
	docker compose exec api alembic upgrade head

measure:
	docker compose exec api python scripts/seed.py --count 100000

loadtest:
	python scripts/loadtest.py --base-url http://localhost:8000

clean:
	rm -f linksnap.db test.db alembic_empty.db
