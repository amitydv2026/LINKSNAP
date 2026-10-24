def test_register_and_login(client):
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "secret123"})
    assert r.status_code == 201
    assert r.json()["email"] == "a@b.com"

    r = client.post("/auth/login", json={"email": "a@b.com", "password": "secret123"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_register_duplicate_email(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "secret123"})
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "secret123"})
    assert r.status_code == 400


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "secret123"})
    r = client.post("/auth/login", json={"email": "a@b.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_create_link_requires_auth(client):
    r = client.post("/links", json={"original_url": "https://example.com"})
    assert r.status_code == 401


def test_invalid_token_rejected(client):
    r = client.post(
        "/links",
        json={"original_url": "https://example.com"},
        headers={"Authorization": "Bearer not.a.real.token"},
    )
    assert r.status_code == 401
