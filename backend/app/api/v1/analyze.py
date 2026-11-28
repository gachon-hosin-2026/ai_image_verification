# API 주소(엔드포인트)를 처리하는 코드
# 1. 요청을 받아 검사하고, 무거운 분석은 스레드풀로 넘김. 그래서 여러 요청이 와도 서버가 안 멈춤
# 2. 결과를 DB 에 저장하고 표준 JSON 으로 돌려줌
from __future__ import annotations

import time
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select

from app.core.config import BASE_DIR, RESULTS_DIR, Settings, get_settings
from app.core.security import SecurityError, read_upload_limited
from app.db.database import SessionLocal
from app.db.models import Analysis, Feedback
from app.pipeline.orchestrator import LoadedModels, PipelineUnavailableError, run_pipeline
from app.pipeline.stage0_preprocess import fetch_image_from_url, preprocess_bytes, simulate_sns_recompression
from app.schemas.analysis import (
    AnalysisResponse,
    AnalyzeUrlRequest,
    FeedbackRequest,
    FeedbackResponse,
    RecompressTestRequest,
    RecompressTestResponse,
)

router = APIRouter(prefix="/api/v1", tags=["analysis"])


# 공통 분석 로직 (스레드풀에서 실행)
# 1. 전처리 → 캐시 확인 → (없으면) 파이프라인 실행 → DB 저장
# 2. 캐시에 있으면 예전 결과를 cached=true 로 바로 돌려줌. 그래서 같은 이미지는 빠르게 응답
def _analyze_sync(
    raw: bytes,
    *,
    settings: Settings,
    models: LoadedModels,
    source_type: str,
    source_url: str | None = None,
    parent_id: str | None = None,
    use_cache: bool = True,
    train_consent: bool = False,
) -> AnalysisResponse:
    started = time.perf_counter()
    pre = preprocess_bytes(raw, source_url=source_url)

    with SessionLocal() as db:
        # 1) 캐시 확인
        if use_cache and settings.CACHE_MATCH != "off":
            key_col = Analysis.phash if settings.CACHE_MATCH == "phash" else Analysis.sha256
            key_val = pre.phash if settings.CACHE_MATCH == "phash" else pre.sha256
            hit = db.scalars(
                select(Analysis)
                .where(key_col == key_val, Analysis.mode == settings.mode, Analysis.source_type != "recompress")
                .order_by(Analysis.created_at.desc())
                .limit(1)
            ).first()
            if hit is not None:
                # 이번에 동의했으면 예전 기록에도 동의 표시 (동의 철회는 여기서 하지 않음)
                if train_consent and not hit.train_consent:
                    hit.train_consent = True
                    db.commit()
                cached = AnalysisResponse.model_validate(hit.result_json)
                return cached.model_copy(update={
                    "cached": True,
                    "latency_ms": int((time.perf_counter() - started) * 1000),
                })

        # 2) 파이프라인 실행
        analysis_id = str(uuid.uuid4())
        result = run_pipeline(pre, analysis_id, settings, models)
        result = result.model_copy(update={"latency_ms": int((time.perf_counter() - started) * 1000)})

        # 3) DB 저장
        db.add(Analysis(
            id=analysis_id,
            mode=settings.mode,
            source_type=source_type,
            source_url=source_url,
            parent_id=parent_id,
            mime=pre.mime,
            width=pre.width,
            height=pre.height,
            sha256=pre.sha256,
            phash=pre.phash,
            train_consent=train_consent,
            original_path=(RESULTS_DIR / f"{analysis_id}_orig{pre.ext}").relative_to(BASE_DIR).as_posix(),
            authenticity_score=result.authenticity_score,
            grade=result.grade.value,
            manipulation_scope=result.manipulation_scope.value,
            latency_ms=result.latency_ms,
            result_json=result.model_dump(mode="json"),
        ))
        db.commit()
        return result


# 스레드풀 실행 + 오류를 한국어 HTTP 응답으로 바꿈
# 1. 보안 오류 → 400/413 / 모델 없음 → 503 / Stage 미구현 → 501
async def _run(func, *args, **kwargs):
    try:
        return await run_in_threadpool(func, *args, **kwargs)
    except SecurityError as e:
        raise HTTPException(e.status_code, e.message) from e
    except PipelineUnavailableError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e)) from e
    except NotImplementedError as e:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, f"{e} (개발 중에는 USE_MOCK_PIPELINE=true 로 실행하세요)") from e


def _models(request: Request) -> LoadedModels:
    return request.app.state.models


# POST /api/v1/analyze/image — 이미지 파일 분석
@router.post("/analyze/image", response_model=AnalysisResponse, summary="이미지 파일 분석")
async def analyze_image(
    request: Request,
    file: UploadFile = File(..., description="JPEG/PNG/WEBP, 최대 20MB"),
    train_consent: bool = Form(False, description="학습 데이터 활용 동의 (선택)"),
):
    settings = get_settings()
    raw = await read_upload_limited(file, settings.max_upload_bytes)
    return await _run(
        _analyze_sync, raw, settings=settings, models=_models(request), source_type="upload", train_consent=train_consent
    )


# POST /api/v1/analyze/url — URL 에서 이미지 추출 후 분석
def _analyze_url_sync(url: str, settings: Settings, models: LoadedModels, train_consent: bool) -> AnalysisResponse:
    raw, image_url = fetch_image_from_url(url, settings.max_upload_bytes, settings.URL_FETCH_TIMEOUT_SEC)
    return _analyze_sync(
        raw, settings=settings, models=models, source_type="url", source_url=image_url, train_consent=train_consent
    )


@router.post("/analyze/url", response_model=AnalysisResponse, summary="URL 이미지 추출 & 분석")
async def analyze_url(request: Request, body: AnalyzeUrlRequest):
    return await _run(_analyze_url_sync, str(body.url), get_settings(), _models(request), body.train_consent)


# POST /api/v1/analyze/recompress-test — SNS 재압축 스트레스 테스트
# 1. 저장해 둔 원본을 50% 축소 + JPEG 75 로 재압축
# 2. 다시 분석해서 원본 점수와 나란히 비교. 그래서 SNS 공유 후에도 판정이 버티는지 확인 가능
def _recompress_sync(analysis_id: str, settings: Settings, models: LoadedModels) -> RecompressTestResponse:
    with SessionLocal() as db:
        row = db.get(Analysis, analysis_id)
        if row is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "해당 analysis_id 의 분석 기록을 찾을 수 없습니다.")
        original = AnalysisResponse.model_validate(row.result_json).model_copy(update={"cached": False})
        orig_path = Path(row.original_path)
        parent_consent = row.train_consent

    if not orig_path.is_absolute():
        orig_path = BASE_DIR / orig_path
    if not orig_path.exists():
        raise HTTPException(status.HTTP_410_GONE, "원본 이미지 파일이 삭제되어 재압축 테스트를 할 수 없습니다.")

    recompressed_bytes = simulate_sns_recompression(orig_path.read_bytes(), scale=0.5, quality=75)
    recompressed = _analyze_sync(
        recompressed_bytes, settings=settings, models=models,
        source_type="recompress", parent_id=analysis_id, use_cache=False, train_consent=parent_consent,
    )
    return RecompressTestResponse(
        analysis_id=analysis_id,
        original_score=original.authenticity_score,
        recompressed_score=recompressed.authenticity_score,
        score_diff=recompressed.authenticity_score - original.authenticity_score,
        original=original,
        recompressed=recompressed,
    )


@router.post("/analyze/recompress-test", response_model=RecompressTestResponse, summary="SNS 재압축 스트레스 테스트")
async def recompress_test(request: Request, body: RecompressTestRequest):
    return await _run(_recompress_sync, body.analysis_id, get_settings(), _models(request))


# POST /api/v1/feedback — 사용자 피드백 저장 (나중에 재학습 데이터로 사용)
def _feedback_sync(body: FeedbackRequest) -> FeedbackResponse:
    with SessionLocal() as db:
        if db.get(Analysis, body.analysis_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "해당 analysis_id 의 분석 기록을 찾을 수 없습니다.")
        fb = Feedback(analysis_id=body.analysis_id, user_label=body.user_label.value, comment=body.comment)
        db.add(fb)
        db.commit()
        return FeedbackResponse(feedback_id=fb.id, analysis_id=fb.analysis_id, status="received")


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED, summary="사용자 피드백 제출")
async def submit_feedback(body: FeedbackRequest):
    return await run_in_threadpool(_feedback_sync, body)
