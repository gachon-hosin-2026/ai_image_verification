# 서버 시작점 코드 (uvicorn app.main:app 으로 실행)
# 1. 서버가 켜질 때 폴더·DB·모델을 한 번만 준비함(lifespan). 그래서 요청마다 모델을 다시 불러오지 않음
# 2. CORS 설정으로 다른 주소(Vercel 프론트엔드)에서 API 호출 허용
# 3. /static/results 를 열어서 프론트엔드가 결과 이미지를 바로 표시할 수 있게 함
# 4. 보안: 분석 API 는 접근 키 필요, IP 별 요청 횟수 제한, 보안 헤더, 키가 있을 때만 /docs 공개
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import Depends, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.analyze import router as analyze_router
from app.core.config import MODELS_DIR, RESULTS_DIR, get_settings
from app.core.security import (
    ACCESS_KEY_HEADER,
    RateLimiter,
    client_ip,
    key_matches,
    require_access_key,
    too_large_message,
)
from app.db.database import init_db
from app.pipeline import stage3_model, stage4_ensemble
from app.pipeline.orchestrator import LoadedModels, ensure_sample_artifacts
from app.schemas.analysis import HealthResponse

logger = logging.getLogger("uvicorn.error")
settings = get_settings()
rate_limiter = RateLimiter(settings.RATE_LIMIT_PER_MIN)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 1번 실행
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    ensure_sample_artifacts()

    if settings.auth_enabled:
        logger.info("🔒 접근 키 사용 중 — 분석 API 와 /docs 는 키가 있어야 열립니다.")
    else:
        logger.warning("⚠️ ACCESS_KEY 가 비어 있습니다. 외부 공개(터널) 전에 .env 에 접근 키를 넣으세요.")

    models = LoadedModels()
    if settings.USE_MOCK_PIPELINE:
        logger.info("🧪 Mock 모드로 시작합니다. (모델 로드 생략)")
    else:
        # 모델은 여기서만 불러옴 (요청마다 불러오기 금지)
        try:
            models.onnx_session = stage3_model.load_model(MODELS_DIR / settings.ONNX_MODEL_FILE)
            models.meta_classifier = stage4_ensemble.load_meta_classifier(MODELS_DIR / settings.META_CLASSIFIER_FILE)
            logger.info("✅ ONNX / XGBoost 모델 로드 완료")
        except (NotImplementedError, FileNotFoundError, OSError) as e:
            # 모델이 없어도 서버는 켜짐. 대신 분석 요청에는 503
            logger.warning("⚠️ 모델 로드 실패: %s", e)
    app.state.models = models
    yield
    # 서버 종료 시 정리
    app.state.models = None


# 접근 키를 쓰면 기본 /docs 를 끄고 아래 보호된 /docs 로 대체
_lock_docs = settings.auth_enabled
app = FastAPI(
    title="AI 이미지 진위 판별 API",
    description="업로드 이미지 또는 뉴스/커뮤니티 URL 이미지가 실사인지 AI 생성인지 판별합니다. "
    "점수가 높을수록 실사, 낮을수록 AI 생성 가능성이 높습니다.\n\n"
    "분석 API 를 테스트하려면 오른쪽 위 **Authorize** 에 접근 키를 넣으세요.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url=None if _lock_docs else "/docs",
    redoc_url=None if _lock_docs else "/redoc",
    openapi_url=None if _lock_docs else "/openapi.json",
)

# 너무 큰 업로드를 미리 차단
# 1. 요청 헤더의 크기(Content-Length)가 20MB+여유분을 넘으면 본문을 받기 전에 413
# 2. 헤더가 없는 경우는 security.read_upload_limited 에서 한 번 더 막음
@app.middleware("http")
async def reject_oversized_upload(request: Request, call_next):
    cl = request.headers.get("content-length")
    if request.method == "POST" and cl and cl.isdigit():
        if int(cl) > settings.max_upload_bytes + 1024 * 1024:  # multipart 헤더 여유분 1MB
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": too_large_message(settings.max_upload_bytes)},
            )
    return await call_next(request)


# 같은 IP 의 분석 요청(POST /api/...) 횟수 제한
# 1. 1분에 RATE_LIMIT_PER_MIN 번을 넘으면 429 + Retry-After(몇 초 뒤 다시) 응답
# 2. 조회(GET)·이미지 보기는 제한하지 않음. 그래서 결과 화면 표시는 영향 없음
@app.middleware("http")
async def limit_request_rate(request: Request, call_next):
    if request.method == "POST" and request.url.path.startswith("/api/"):
        wait = rate_limiter.check(client_ip(request))
        if wait:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": f"요청이 너무 많습니다. {wait}초 후에 다시 시도하세요."},
                headers={"Retry-After": str(wait)},
            )
    return await call_next(request)


# 모든 응답에 기본 보안 헤더 추가
# 1. nosniff: 브라우저가 파일 형식을 멋대로 추측해 스크립트로 실행하는 것 방지
# 2. DENY: 다른 사이트가 이 서버 화면을 iframe 으로 몰래 띄우는 것(클릭재킹) 방지
# 3. no-referrer: 외부로 나갈 때 접속 주소(키 포함 가능)가 전달되지 않게 함
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    return response


# CORS 는 가장 바깥에 둠 (마지막에 추가한 미들웨어가 가장 먼저 실행됨)
# 1. 그래서 413·429 같은 차단 응답에도 CORS 헤더가 붙어, 프론트에서 한국어 오류 메시지를 읽을 수 있음
_origins = settings.allow_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials="*" not in _origins,  # "*" 일 때는 credentials 를 켤 수 없음
    allow_methods=["*"],
    allow_headers=["*"],
)


# 요청 필드가 틀렸을 때(422) 한국어 메시지로 응답
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "요청 형식이 올바르지 않습니다. 필드 이름과 값을 확인하세요.", "errors": jsonable_encoder(exc.errors())},
    )


app.mount("/static/results", StaticFiles(directory=RESULTS_DIR), name="results")
# 분석·피드백 API 전체에 접근 키 검사 적용
app.include_router(analyze_router, dependencies=[Depends(require_access_key)])


@app.get("/", response_model=HealthResponse, tags=["health"])
@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", mode=settings.mode, version=settings.APP_VERSION)


# ── 키로 보호된 /docs (ACCESS_KEY 가 있을 때만 사용) ─────────
# 1. /docs 에 들어오면 접근 키 입력 화면을 보여줌
# 2. 키가 맞으면 Swagger 화면을 띄우고, 그 화면이 /openapi.json?key=... 로 API 목록을 받아옴
# 3. 키가 틀리면 API 목록(어떤 주소가 있는지)도 보여주지 않음
if _lock_docs:

    def _key_from(request: Request) -> str | None:
        return request.query_params.get("key") or request.headers.get(ACCESS_KEY_HEADER)

    @app.get("/openapi.json", include_in_schema=False)
    async def protected_openapi(request: Request):
        if not key_matches(_key_from(request), settings.ACCESS_KEY):
            return JSONResponse(status_code=401, content={"detail": "접근 키가 필요합니다."})
        return JSONResponse(app.openapi())

    @app.get("/docs", include_in_schema=False)
    async def protected_docs(request: Request):
        key = _key_from(request)
        if key_matches(key, settings.ACCESS_KEY):
            return get_swagger_ui_html(
                openapi_url=f"/openapi.json?key={quote(key or '')}",
                title="AI 이미지 진위 판별 API — 문서",
                swagger_ui_parameters={"persistAuthorization": True},
            )
        wrong = key is not None
        return HTMLResponse(_DOCS_LOGIN_HTML.replace("{{msg}}", "접근 키가 올바르지 않습니다." if wrong else ""), status_code=401 if wrong else 200)


_DOCS_LOGIN_HTML = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>API 문서 — 접근 키</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#000;color:#fff;font-family:system-ui,sans-serif}
form{background:rgba(255,255,255,.05);padding:28px;border-radius:20px;width:min(340px,90vw)}
h1{font-size:18px;margin:0 0 6px}p{color:rgba(235,235,245,.6);font-size:13px;margin:0 0 18px}
input{width:100%;box-sizing:border-box;height:40px;border-radius:10px;border:0;background:rgba(255,255,255,.08);color:#fff;padding:0 12px;font-size:14px}
button{margin-top:10px;width:100%;height:40px;border-radius:10px;border:0;background:#fff;color:#000;font-weight:600;cursor:pointer}
.err{color:#ff453a;font-size:12px;margin-top:10px;min-height:14px}</style></head>
<body><form method="get" action="/docs"><h1>API 문서</h1><p>팀에서 받은 접근 키를 입력하세요.</p>
<input name="key" type="password" placeholder="접근 키" autofocus required><button>열기</button>
<div class="err">{{msg}}</div></form></body></html>"""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=settings.PORT)
