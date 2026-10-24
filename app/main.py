"""LinkSnap FastAPI application factory."""
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.routes import auth, links, redirect

app = FastAPI(
    title="LinkSnap",
    version="1.0.0",
    description="A URL shortener with click tracking, an LRU redirect cache, "
    "and transactional click recording.",
)

# Serve the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root() -> FileResponse:
    return FileResponse("static/index.html")


# Auth and links routers first, then the catch-all /{short_code} last.
app.include_router(auth.router)
app.include_router(links.router)
app.include_router(redirect.router)
