# API 동작 테스트 (GitHub Actions 가 PR 마다 자동 실행)
# 1. 명세서의 고정 API 계약(JSON 필드·Enum)이 깨지지 않았는지 확인
# 2. 보안 기능(접근 키, 파일 형식 검사, SSRF 차단, 요청 횟수 제한)이 동작하는지 확인
# 3. 실행: backend 폴더에서 pytest
from app.core.security import RateLimiter
from app.pipeline.stage4_ensemble import score_to_grade
from app.schemas.analysis import Grade

CONTRACT_KEYS = {
    "analysis_id", "cached", "authenticity_score", "grade", "manipulation_scope",
    "latency_ms", "metrics", "breakdown", "visual_artifacts",
}


# ── 상태 확인 ──
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "mode": "mock", "version": "1.0.0"}


# ── 이미지 분석: 계약 형식 ──
def test_analyze_image_contract(client, auth, jpeg_bytes):
    r = client.post("/api/v1/analyze/image", headers=auth, files={"file": ("a.jpg", jpeg_bytes, "image/jpeg")})
    assert r.status_code == 200
    d = r.json()
    assert set(d) == CONTRACT_KEYS
    assert 0 <= d["authenticity_score"] <= 100
    assert d["grade"] == score_to_grade(d["authenticity_score"]).value
    assert [b["factor"] for b in d["breakdown"]] == ["딥러닝 시각 패턴 분석", "FFT 고주파 스펙트럼", "ELA 압축 잔차", "EXIF 메타데이터"]
    # EXIF 없음은 절대 감점하지 않음 (중립 규칙)
    assert d["breakdown"][3]["delta"] == 0
    # 결과 이미지는 키 없이도 열려야 함 (프론트 <img> 표시용)
    for url in d["visual_artifacts"].values():
        assert client.get(url).status_code == 200


def test_png_also_ok(client, auth, png_bytes):
    r = client.post("/api/v1/analyze/image", headers=auth, files={"file": ("a.png", png_bytes, "image/png")})
    assert r.status_code == 200


# ── 보안 ──
def test_requires_access_key(client, jpeg_bytes):
    r = client.post("/api/v1/analyze/image", files={"file": ("a.jpg", jpeg_bytes, "image/jpeg")})
    assert r.status_code == 401
    r = client.post("/api/v1/analyze/image", headers={"X-Access-Key": "wrong"}, files={"file": ("a.jpg", jpeg_bytes, "image/jpeg")})
    assert r.status_code == 401


def test_rejects_fake_image(client, auth):
    r = client.post("/api/v1/analyze/image", headers=auth, files={"file": ("fake.jpg", b"not an image", "image/jpeg")})
    assert r.status_code == 400


def test_blocks_private_url(client, auth):
    for url in ["http://127.0.0.1/a.jpg", "http://169.254.169.254/latest", "http://192.168.0.1/x.png", "http://10.0.0.1/"]:
        r = client.post("/api/v1/analyze/url", headers=auth, json={"url": url})
        assert r.status_code == 400, url


def test_docs_locked_without_key(client):
    assert client.get("/openapi.json").status_code == 401
    assert client.get("/openapi.json", params={"key": "test-access-key"}).status_code == 200


def test_security_headers(client):
    h = client.get("/health").headers
    assert h["x-content-type-options"] == "nosniff"
    assert h["x-frame-options"] == "DENY"


def test_rate_limiter_blocks_after_limit():
    rl = RateLimiter(per_minute=3)
    assert [rl.check("1.2.3.4") for _ in range(3)] == [0, 0, 0]
    assert rl.check("1.2.3.4") > 0          # 4번째는 막힘
    assert rl.check("5.6.7.8") == 0         # 다른 IP 는 영향 없음


# ── 재압축 테스트 · 피드백 ──
def test_recompress_and_feedback(client, auth, jpeg_bytes):
    aid = client.post("/api/v1/analyze/image", headers=auth, files={"file": ("a.jpg", jpeg_bytes, "image/jpeg")}).json()["analysis_id"]

    r = client.post("/api/v1/analyze/recompress-test", headers=auth, json={"analysis_id": aid})
    assert r.status_code == 200
    d = r.json()
    assert d["score_diff"] == d["recompressed_score"] - d["original_score"]

    r = client.post("/api/v1/feedback", headers=auth, json={"analysis_id": aid, "user_label": "AI"})
    assert r.status_code == 201
    assert client.post("/api/v1/feedback", headers=auth, json={"analysis_id": "nope", "user_label": "AI"}).status_code == 404


# ── 점수 방향 (절대 반전 금지) ──
def test_grade_boundaries():
    assert score_to_grade(100) == Grade.SAFE_LIKELY_REAL
    assert score_to_grade(80) == Grade.SAFE_LIKELY_REAL
    assert score_to_grade(79) == Grade.CAUTION_EDITED_OR_RECOMPRESSED
    assert score_to_grade(55) == Grade.CAUTION_EDITED_OR_RECOMPRESSED
    assert score_to_grade(54) == Grade.WARNING_AI_SUSPECTED
    assert score_to_grade(30) == Grade.WARNING_AI_SUSPECTED
    assert score_to_grade(29) == Grade.DANGER_HIGHLY_LIKELY_AI
    assert score_to_grade(0) == Grade.DANGER_HIGHLY_LIKELY_AI


# ── 학습 데이터 동의 ──
def test_train_consent_saved(client, auth, png_bytes):
    from app.db.database import SessionLocal
    from app.db.models import Analysis

    yes = client.post(
        "/api/v1/analyze/image", headers=auth,
        files={"file": ("y.png", png_bytes, "image/png")}, data={"train_consent": "true"},
    ).json()["analysis_id"]
    no = client.post(
        "/api/v1/analyze/image", headers=auth, files={"file": ("n.png", png_bytes, "image/png")}
    ).json()["analysis_id"]
    with SessionLocal() as db:
        assert db.get(Analysis, yes).train_consent is True
        assert db.get(Analysis, no).train_consent is False   # 기본값은 동의 안 함


def test_old_db_gets_new_column(tmp_path):
    # 예전 버전 DB(train_consent 컬럼 없음)에 서버를 켜면 컬럼이 자동으로 추가돼야 함
    from sqlalchemy import create_engine, inspect, text

    from app.db.database import _add_missing_columns

    eng = create_engine(f"sqlite:///{tmp_path}/old.db")
    with eng.begin() as c:
        c.execute(text("CREATE TABLE analyses (id VARCHAR(36) PRIMARY KEY, phash VARCHAR(64))"))
        c.execute(text("INSERT INTO analyses (id, phash) VALUES ('a', 'b')"))
    _add_missing_columns(eng)
    assert "train_consent" in {col["name"] for col in inspect(eng).get_columns("analyses")}
    with eng.connect() as c:
        assert c.execute(text("SELECT train_consent FROM analyses")).scalar() == 0  # 기존 기록은 '동의 안 함'
