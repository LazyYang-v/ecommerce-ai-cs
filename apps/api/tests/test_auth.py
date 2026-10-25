def _register(client, email, password="password123", nickname=None):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "nickname": nickname},
    )


def _login(client, email, password="password123"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_register_returns_user_without_secrets(make_api_client):
    with make_api_client() as client:
        resp = _register(client, "alice@test.com", nickname="Alice")
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "alice@test.com"
        assert body["nickname"] == "Alice"
        assert body["role"] == "customer"
        assert "password_hash" not in body
        assert "password" not in body


def test_register_normalizes_email_and_rejects_duplicate(make_api_client):
    with make_api_client() as client:
        assert _register(client, "Bob@test.com").status_code == 201
        # 大小写不同的同一邮箱视为重复
        resp = _register(client, "bob@test.com")
        assert resp.status_code == 409


def test_register_validates_input(make_api_client):
    with make_api_client() as client:
        assert _register(client, "not-an-email").status_code == 422
        assert (
            _register(client, "ok@test.com", password="short").status_code == 422
        )


def test_login_returns_bearer_token(make_api_client):
    with make_api_client() as client:
        _register(client, "carol@test.com")
        resp = _login(client, "carol@test.com")
        assert resp.status_code == 200
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]
        # token 可用于受保护接口
        me = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {body['access_token']}"},
        )
        assert me.status_code == 200
        assert me.json()["email"] == "carol@test.com"


def test_login_wrong_password(make_api_client):
    with make_api_client() as client:
        _register(client, "dave@test.com")
        resp = _login(client, "dave@test.com", "wrong-password")
        assert resp.status_code == 401


def test_login_unknown_email_same_error(make_api_client):
    with make_api_client() as client:
        resp = _login(client, "ghost@test.com")
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Incorrect email or password"


def test_protected_endpoint_requires_valid_token(make_api_client):
    with make_api_client() as client:
        assert client.get("/api/v1/orders").status_code == 401
        bad = client.get(
            "/api/v1/orders", headers={"Authorization": "Bearer not-a-jwt"}
        )
        assert bad.status_code == 401
        fake = client.get(
            "/api/v1/orders",
            headers={
                "Authorization": (
                    "Bearer eyJhbGciOiJIUzI1NiJ9."
                    "eyJzdWIiOiI4M2YxYjM0Yy00ZDZlLTQ2ZjMtOGIzNy0wYThkMmY5ZTFmMjEifQ."
                    "invalid-signature"
                )
            },
        )
        assert fake.status_code == 401
