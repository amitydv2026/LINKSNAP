def test_redirect_records_click_and_caches(auth_headers, client):
    create = client.post(
        "/links",
        json={"original_url": "https://example.com/target"},
        headers=auth_headers,
    )
    code = create.json()["short_code"]
    link_id = create.json()["id"]

    # First hit: DB lookup, cache MISS, click recorded.
    r = client.get(f"/{code}", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "https://example.com/target"
    assert r.headers["x-cache"] == "MISS"

    # Second hit: served from the LRU cache.
    r2 = client.get(f"/{code}", follow_redirects=False)
    assert r2.headers["x-cache"] == "HIT"

    # Two clicks recorded, counter incremented twice.
    stats = client.get(f"/links/{link_id}/stats", headers=auth_headers).json()
    assert stats["click_count"] == 2
    assert len(stats["recent_clicks"]) == 2


def test_redirect_not_found(client):
    r = client.get("/nope123", follow_redirects=False)
    assert r.status_code == 404
