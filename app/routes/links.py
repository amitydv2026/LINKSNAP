"""Link management routes: create a short link and view stats."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Click, Link, User
from app.schemas import LinkCreate, LinkOut, LinkStats
from app.services.auth import get_current_user
from app.services.shortcode import create_unique_short_code

router = APIRouter(prefix="/links", tags=["links"])


@router.post("", response_model=LinkOut, status_code=status.HTTP_201_CREATED)
def create_link(
    payload: LinkCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Link:
    code = create_unique_short_code(db)
    link = Link(
        user_id=user.id,
        short_code=code,
        original_url=str(payload.original_url),
        click_count=0,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.get("/{link_id}/stats", response_model=LinkStats)
def link_stats(
    link_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LinkStats:
    link = db.get(Link, link_id)
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    if link.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed to view this link")
    recent_clicks = (
        db.query(Click)
        .filter(Click.link_id == link_id)
        .order_by(Click.clicked_at.desc())
        .limit(20)
        .all()
    )
    return LinkStats(
        id=link.id,
        short_code=link.short_code,
        original_url=link.original_url,
        click_count=link.click_count,
        recent_clicks=recent_clicks,
    )
