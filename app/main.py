"""LinkSnap FastAPI application factory."""
from fastapi import FastAPI

from app.routes import auth, links, redirect

app = FastAPI(
    title="LinkSnap",
    version="1.0.0",
    description="A URL shortener with click tracking, an LRU redirect cache, "
    "and transactional click recording.",
)

# Order matters: specific routers first, the catch-all /{short_code} last.
app.include_router(auth.router)
app.include_router(links.router)
app.include_router(redirect.router)


@app.get("/")
def root() -> dict:
    return {"name": "LinkSnap", "status": "ok"}
