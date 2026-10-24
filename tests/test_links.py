def test_create_link(auth_headers, client):
    r = client.post(
        "/links",
        json={"original_url": "https://example.com/long"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert len(body["short_code"]) == 7
    assert body["original_url"] == "https://example.com/long"
    assert body["click_count"] == 0


def test_stats_owner_only(auth_headers, client):
    create = client.post(
        "/links",
        json={"original_url": "https://example.com"},
        headers=auth_headers,
    )
    link_id = create.json()["id"]

    # A second, different user must not see the first user's stats.
    client.post("/auth/register", json={"email": "other@test.com", "password": "secret123"})
    tok = client.post(
        "/auth/login", json={"email": "other@test.com", "password": "secret123"}
    ).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {tok}"}

    r = client.get(f"/links/{link_id}/stats", headers=other_headers)
    assert r.status_code == 403

    r = client.get(f"/links/{link_id}/stats", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["click_count"] == 0


def test_stats_not_found(auth_headers, client):
    r = client.get("/links/999999/stats", headers=auth_headers)
    assert r.status_code == 404
