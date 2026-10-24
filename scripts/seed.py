"""Seed ~100k links and measure short_code lookup performance via EXPLAIN ANALYZE.

Must run against Postgres (SQLite has no EXPLAIN ANALYZE timing). Use Docker:

    make up
    make measure

Prints the short_code lookup time WITH the unique index and WITHOUT it (after
dropping the constraint), plus a speedup factor. Paste these numbers into the
README.
"""
import argparse
import random
import re
import time

from sqlalchemy import create_engine, insert, inspect, text
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Link, User
from app.services.auth import hash_password
from app.services.shortcode import _ALPHABET


def gen_code(length=7):
    return "".join(random.choices(_ALPHABET, k=length))


def unique_codes(n, length=7):
    seen: set[str] = set()
    out: list[str] = []
    while len(out) < n:
        code = gen_code(length)
        if code not in seen:
            seen.add(code)
            out.append(code)
    return out


def seed(db: Session, count: int) -> str:
    user = db.query(User).filter(User.email == "seeder@test.com").first()
    if user is None:
        user = User(email="seeder@test.com", password_hash=hash_password("seedpass"))
        db.add(user)
        db.commit()
        db.refresh(user)

    codes = unique_codes(count)
    rows = [
        {"user_id": user.id, "short_code": c, "original_url": f"https://example.com/page/{i}", "click_count": 0}
        for i, c in enumerate(codes)
    ]
    batch = 5000
    t0 = time.time()
    for i in range(0, len(rows), batch):
        db.execute(insert(Link), rows[i : i + batch])
        db.commit()
    print(f"Inserted {count} links in {time.time() - t0:.1f}s")
    return codes[0]


def unique_constraint_name(engine, table="links", column="short_code"):
    for uc in inspect(engine).get_unique_constraints(table):
        if column in uc["column_names"]:
            return uc["name"]
    return None


def explain_timing(db: Session, code: str):
    rows = db.execute(
        text("EXPLAIN ANALYZE SELECT id FROM links WHERE short_code = :c"), {"c": code}
    ).fetchall()
    plan = "\n".join(r[0] for r in rows)
    m = re.search(r"Execution Time:\s*([\d.]+)\s*ms", plan)
    return (float(m.group(1)) if m else -1.0), plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=100000)
    args = ap.parse_args()

    if not settings.database_url.startswith("postgresql"):
        raise SystemExit("seed.py must run against Postgres. Set DATABASE_URL or run via `make measure`.")

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with Session(engine) as db:
        code = seed(db, args.count)

        t_with, plan_with = explain_timing(db, code)

        name = unique_constraint_name(engine)
        if name:
            db.execute(text(f'ALTER TABLE links DROP CONSTRAINT "{name}"'))
            db.commit()
        else:
            print("WARNING: no unique constraint found on links.short_code")

        t_without, plan_without = explain_timing(db, code)

        db.execute(text("CREATE UNIQUE INDEX ux_links_short_code ON links (short_code)"))
        db.commit()

    print("\n=== EXPLAIN ANALYZE: short_code lookup ===")
    print(f"WITH index    : {t_with:.3f} ms")
    print(f"WITHOUT index : {t_without:.3f} ms")
    print(f"speedup       : {t_without / t_with:.1f}x")
    print("\n--- plan WITH index ---")
    print(plan_with)
    print("\n--- plan WITHOUT index ---")
    print(plan_without)


if __name__ == "__main__":
    main()
