import os

import pytest
from fastapi.testclient import TestClient

# 必须在导入 app 前设置，Settings 读取环境变量
os.environ.setdefault("INTERNAL_SERVICE_TOKEN", "test-internal-token")

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
