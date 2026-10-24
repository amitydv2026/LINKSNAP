"""Skewed-distribution load test for the redirect endpoint.

Hits a few "hot" short codes most of the time (like real marketing traffic) and
reports the cache hit rate, read from the X-Cache response header.

    BASE_URL=http://localhost:8000 python scripts/loadtest.py --requests 5000
    # or via Make against the Docker stack:
    make up && make loadtest
"""
import argparse
import random
import time

import httpx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--requests", type=int, default=5000)
    ap.add_argument("--links", type=int, default=2000, help="links to create before testing")
    ap.add_argument("--hot", type=int, default=10, help="number of popular codes")
    ap.add_argument("--hot-weight", type=float, default=0.8, help="probability a request hits a hot code")
    args = ap.parse_args()

    base = args.base_url.rstrip("/")
    with httpx.Client(base_url=base, timeout=30.0) as client:
        client.post("/auth/register", json={"email": "load@test.com", "password": "secret123"})
        tok = client.post(
            "/auth/login", json={"email": "load@test.com", "password": "secret123"}
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {tok}"}

        print(f"Creating {args.links} links...")
        codes = []
        for i in range(args.links):
            r = client.post("/links", json={"original_url": f"https://example.com/{i}"}, headers=headers)
            codes.append(r.json()["short_code"])
        hot = codes[: args.hot]

        hits = misses = 0
        t0 = time.time()
        for _ in range(args.requests):
            code = random.choice(hot) if random.random() < args.hot_weight else random.choice(codes)
            r = client.get(f"/{code}", follow_redirects=False)
            cache = r.headers.get("x-cache", "")
            if cache == "HIT":
                hits += 1
            elif cache == "MISS":
                misses += 1
        elapsed = time.time() - t0

    total = hits + misses
    print("\n=== Load test results ===")
    print(f"requests      : {args.requests}")
    print(f"elapsed       : {elapsed:.2f}s  ({args.requests / elapsed:.0f} req/s)")
    print(f"cache hits    : {hits}")
    print(f"cache misses  : {misses}")
    print(f"cache hit rate: {hits / total * 100:.1f}%" if total else "cache hit rate: n/a")


if __name__ == "__main__":
    main()
