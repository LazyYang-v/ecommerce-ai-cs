def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "agent"


def test_health_response_carries_request_id_header(client):
    resp = client.get("/health", headers={"X-Request-ID": "req-health-001"})
    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"] == "req-health-001"
