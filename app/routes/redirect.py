"""The key endpoint: GET /{short_code} resolves a short link and records a click.

A click is recorded by inserting a `clicks` row AND incrementing the link's
`click_count` inside a single DB transaction. If either operation fails the
whole transaction is rolled back, so the counter and the click log never drift
apart.

An LRU cache sits in front of the short_code lookup so hot links skip the
(indexed) database read. The click is still written on every redirect.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.cache.lru import LRUCache
from app.config import settings
from app.database import get_db
from app.models import Click, Link

router = APIRouter(tags=["redirect"])

# Module-level cache shared across requests. The value is (link_id, original_url).
redirect_cache = LRUCache(capacity=settings.lru_cache_size)


def increment_click_count(db: Session, link_id: int) -> None:
    """Atomically bump the counter via a single UPDATE. Patchable for tests."""
    db.query(Link).filter(Link.id == link_id).update({Link.click_count: Link.click_count + 1})
    db.flush()


def record_click(db: Session, link_id: int, user_agent: str | None) -> None:
    """Insert a click row and increment the counter in one transaction.

    If either step fails the transaction is rolled back so the click log and the
    counter stay consistent.
    """
    try:
        db.add(Click(link_id=link_id, user_agent=(user_agent or "")[:512]))
        db.flush()
        increment_click_count(db, link_id)
        db.commit()
    except Exception:
        db.rollback()
        raise


@router.get("/{short_code}")
def redirect(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    cached = redirect_cache.get(short_code)
    if cached is not None:
        link_id, original_url = cached
        record_click(db, link_id, request.headers.get("user-agent"))
        return RedirectResponse(
            url=original_url, status_code=status.HTTP_302_FOUND, headers={"X-Cache": "HIT"}
        )

    link = db.query(Link).filter(Link.short_code == short_code).first()
    if link is None:
        raise HTTPException(status_code=404, detail="Short link not found")
    redirect_cache.put(short_code, (link.id, link.original_url))
    record_click(db, link.id, request.headers.get("user-agent"))
    return RedirectResponse(
        url=link.original_url, status_code=status.HTTP_302_FOUND, headers={"X-Cache": "MISS"}
    )
