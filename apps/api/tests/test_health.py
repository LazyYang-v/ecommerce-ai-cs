def test_health_returns_ok(make_api_client):
    with make_api_client() as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok", "service": "business-api"}


def test_health_echoes_request_id_header(make_api_client):
    with make_api_client() as client:
        resp = client.get("/health", headers={"X-Request-ID": "req-h-1"})
        assert resp.status_code == 200
        assert resp.headers["X-Request-ID"] == "req-h-1"
