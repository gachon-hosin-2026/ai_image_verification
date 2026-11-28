# 테스트 공통 준비 코드
# 1. 앱을 불러오기 전에 테스트용 환경 변수를 먼저 설정함. 그래서 내 .env 나 실제 DB 를 건드리지 않음
# 2. client: 서버를 실제로 띄우지 않고 요청을 보내볼 수 있는 테스트 클라이언트 (lifespan 포함)
# 3. 이미지 픽스처: 테스트용 JPEG / PNG / 가짜 파일을 메모리에서 만듦
import io
import os
import tempfile

import numpy as np
import pytest
from PIL import Image

TEST_KEY = "test-access-key"
_tmp = tempfile.mkdtemp()
os.environ.update(
    {
        "USE_MOCK_PIPELINE": "true",
        "MOCK_SCORE_MODE": "fixed",
        "ACCESS_KEY": TEST_KEY,
        "RATE_LIMIT_PER_MIN": "1000",  # 일반 테스트는 제한에 안 걸리게 (제한 자체는 따로 테스트)
        "DATABASE_URL": f"sqlite:///{_tmp}/test.db",
        "CACHE_MATCH": "off",
        "ALLOW_ORIGINS": "*",
    }
)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth():
    return {"X-Access-Key": TEST_KEY}


def _image_bytes(fmt: str) -> bytes:
    rng = np.random.default_rng(0)
    arr = (rng.random((120, 160, 3)) * 255).astype("uint8")
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture
def jpeg_bytes():
    return _image_bytes("JPEG")


@pytest.fixture
def png_bytes():
    return _image_bytes("PNG")
