"""Verifies the redirect click transaction rolls back atomically on failure."""
import pytest

from app.models import Click, Link, User
from app.routes.redirect import record_click


def test_record_click_rolls_back_on_failure(db, monkeypatch):
    # Set up a committed link to record clicks against.
    user = User(email="t@t.com", password_hash="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    link = Link(
        user_id=user.id,
        short_code="abc1234",
        original_url="https://example.com",
        click_count=0,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    # Force the counter increment to fail after the click row is flushed.
    def boom(db, link_id):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr("app.routes.redirect.increment_click_count", boom)

    with pytest.raises(RuntimeError):
        record_click(db, link.id, "UA-test")

    # The flushed click row must have been rolled back (atomicity).
    assert db.query(Click).count() == 0
    # The counter must be unchanged.
    db.refresh(link)
    assert link.click_count == 0
