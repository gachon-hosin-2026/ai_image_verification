# 분석 전체 흐름을 순서대로 실행하는 코드 (Stage 0 → 5)
# 1. USE_MOCK_PIPELINE=true 면 Mock 결과(고정 JSON + 가짜 히트맵)를 만듦. 그래서 AI 없이도 프론트엔드 개발 가능
# 2. false 면 Stage 1~5 를 차례로 호출해 실제 점수를 계산함
# 3. CPU 를 많이 쓰므로 API 쪽에서 run_in_threadpool 로 호출함. 그래서 분석 중에도 서버가 멈추지 않음
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from app.core.config import RESULTS_DIR, Settings
from app.pipeline import stage1_metadata, stage2_forensics, stage3_model, stage4_ensemble, stage5_report
from app.pipeline.stage0_preprocess import PreprocessResult
from app.schemas.analysis import (
    AnalysisResponse,
    BreakdownItem,
    Grade,
    ManipulationScope,
    Metrics,
    VisualArtifacts,
)

STATIC_PREFIX = "/static/results"
DISPLAY_MAX_SIDE = 1024  # 화면 표시용 이미지 최대 크기 (분석에는 사용 안 함)


# Production 모드인데 모델이 안 불러와졌을 때 쓰는 오류 (→ 503)
class PipelineUnavailableError(RuntimeError):
    pass


# 서버 시작 때 한 번만 불러온 모델 보관함 (app.state.models)
@dataclass
class LoadedModels:
    onnx_session: Any = None
    meta_classifier: Any = None

    @property
    def ready(self) -> bool:
        return self.onnx_session is not None and self.meta_classifier is not None


# 분석 1건의 결과 이미지 경로 (원본 / Grad-CAM / ELA)
@dataclass
class ArtifactPaths:
    original: Path
    gradcam: Path
    ela: Path

    @classmethod
    def for_id(cls, analysis_id: str, ext: str) -> "ArtifactPaths":
        return cls(
            original=RESULTS_DIR / f"{analysis_id}_orig{ext}",
            gradcam=RESULTS_DIR / f"{analysis_id}_gradcam.png",
            ela=RESULTS_DIR / f"{analysis_id}_ela.png",
        )

    def urls(self) -> VisualArtifacts:
        return VisualArtifacts(
            original_url=f"{STATIC_PREFIX}/{self.original.name}",
            gradcam_url=f"{STATIC_PREFIX}/{self.gradcam.name}",
            ela_url=f"{STATIC_PREFIX}/{self.ela.name}",
        )


# 분석 1건 실행
# 1. 원본을 재인코딩 없이 그대로 저장. 그래서 재압축 테스트 때 진짜 원본을 다시 쓸 수 있음
# 2. Mock / Production 중 하나로 분기
# 3. latency_ms 와 cached 는 API 쪽에서 채움
def run_pipeline(
    pre: PreprocessResult,
    analysis_id: str,
    settings: Settings,
    models: LoadedModels,
) -> AnalysisResponse:
    paths = ArtifactPaths.for_id(analysis_id, pre.ext)
    paths.original.write_bytes(pre.raw_bytes)

    if settings.USE_MOCK_PIPELINE:
        return _run_mock(pre, analysis_id, settings, paths)
    return _run_production(pre, analysis_id, models, paths)


# Production 경로
# 1. Stage 1·2 는 원본, Stage 3 은 리사이즈 텐서 사용 (Dual-Path)
# 2. 수치를 모아 Stage 4 로 점수, Stage 5 로 범위·설명 생성
def _run_production(pre: PreprocessResult, analysis_id: str, models: LoadedModels, paths: ArtifactPaths) -> AnalysisResponse:
    if not models.ready:
        raise PipelineUnavailableError("AI 모델이 로드되지 않았습니다. models/ 폴더의 가중치 파일을 확인하세요.")

    meta = stage1_metadata.analyze_metadata(pre.raw_bytes, pre.exif_bytes, pre.mime)            # 원본 경로
    forensics = stage2_forensics.analyze_forensics(pre.original_rgb, pre.raw_bytes, pre.mime, paths.ela)  # 원본 경로
    model = stage3_model.run_model(models.onnx_session, pre.model_tensor, pre.original_rgb, paths.gradcam)  # 리사이즈 경로

    features = {
        "dl_human_prob": model.dl_human_prob,
        "fft_hf_ratio": forensics.fft_hf_ratio,
        "fft_slope": forensics.fft_slope,
        "ela_mean": forensics.ela_mean,
        "ela_std": forensics.ela_std,
        "ela_top5_concentration": forensics.ela_top5_concentration,
        "meta_status_code": float(meta.status_code),
    }
    ensemble = stage4_ensemble.compute_score(features, models.meta_classifier)
    report = stage5_report.build_report(ensemble, model, forensics, meta)

    return AnalysisResponse(
        analysis_id=analysis_id,
        cached=False,
        authenticity_score=ensemble.authenticity_score,
        grade=ensemble.grade,
        manipulation_scope=report.manipulation_scope,
        latency_ms=0,
        metrics=Metrics(**{**features, "meta_status_code": meta.status_code}),
        breakdown=report.breakdown,
        visual_artifacts=paths.urls(),
    )


# Mock 경로에서 쓰는 고정값 (명세서 예시 JSON 과 동일)
_SAMPLE_METRICS = Metrics(
    dl_human_prob=0.31, fft_hf_ratio=0.142, fft_slope=-1.85,
    ela_mean=4.2, ela_std=18.4, ela_top5_concentration=0.22, meta_status_code=0,
)

_MOCK_DETAILS = {
    Grade.SAFE_LIKELY_REAL: ("자연스러운 촬영 텍스처 패턴", "자연 영상 수준의 고주파 분포", "압축 잔차 분포 정상"),
    Grade.CAUTION_EDITED_OR_RECOMPRESSED: ("일부 영역 텍스처 불일치", "재압축으로 인한 고주파 손실 가능성", "국소 영역 잔차 편중"),
    Grade.WARNING_AI_SUSPECTED: ("생성형 AI 특유의 텍스처 및 경계 왜곡 감지", "고주파 대역 비정상 감쇠 패턴 확인", "전역 픽셀 잔차 분산 이상"),
    Grade.DANGER_HIGHLY_LIKELY_AI: ("생성형 AI 특유의 패턴이 강하게 감지됨", "고주파 스펙트럼이 생성 모델 특성과 일치", "전역적으로 균일한 비정상 잔차"),
}
_EXIF_NEUTRAL_DETAIL = "정보 없음 (SNS 재압축 가능성으로 중립 처리)"

_GRADE_TO_SCOPE = {
    Grade.SAFE_LIKELY_REAL: ManipulationScope.LIKELY_AUTHENTIC,
    Grade.CAUTION_EDITED_OR_RECOMPRESSED: ManipulationScope.LOCAL_EDIT_SUSPECTED,
    Grade.WARNING_AI_SUSPECTED: ManipulationScope.GLOBAL_AI_GENERATED,
    Grade.DANGER_HIGHLY_LIKELY_AI: ManipulationScope.GLOBAL_AI_GENERATED,
}


# Mock 결과 만들기
# 1. fixed 모드 = 항상 38점 / hash 모드 = 이미지마다 다른 점수(같은 이미지는 같은 점수)
# 2. 100점에서 깎인 점수를 42:14:6 비율로 나눔. 그래서 delta 합계가 항상 (점수 - 100) 과 맞음
# 3. 가짜 Grad-CAM·ELA 이미지("MOCK" 표시)를 저장
def _run_mock(pre: PreprocessResult, analysis_id: str, settings: Settings, paths: ArtifactPaths) -> AnalysisResponse:
    if settings.MOCK_SCORE_MODE == "hash":
        score = int(pre.phash, 16) % 101  # 같은 이미지는 항상 같은 점수
        metrics = _SAMPLE_METRICS.model_copy(update={"dl_human_prob": round(score / 100, 2)})
    else:
        score = 38  # 명세서 예시값
        metrics = _SAMPLE_METRICS

    grade = stage4_ensemble.score_to_grade(score)
    total = 100 - score
    dl = -round(total * 42 / 62)
    fft = -round(total * 14 / 62)
    ela = -total - dl - fft
    dl_d, fft_d, ela_d = _MOCK_DETAILS[grade]

    _write_mock_gradcam(pre.original_rgb, paths.gradcam)
    _write_mock_ela(pre.original_rgb, paths.ela)

    return AnalysisResponse(
        analysis_id=analysis_id,
        cached=False,
        authenticity_score=score,
        grade=grade,
        manipulation_scope=_GRADE_TO_SCOPE[grade],
        latency_ms=0,
        metrics=metrics,
        breakdown=[
            BreakdownItem(factor="딥러닝 시각 패턴 분석", delta=dl, detail=dl_d),
            BreakdownItem(factor="FFT 고주파 스펙트럼", delta=fft, detail=fft_d),
            BreakdownItem(factor="ELA 압축 잔차", delta=ela, detail=ela_d),
            BreakdownItem(factor="EXIF 메타데이터", delta=0, detail=_EXIF_NEUTRAL_DETAIL),
        ],
        visual_artifacts=paths.urls(),
    )


# Mock 가짜 이미지 만들기
# 화면 표시용 축소본 (분석용이 아니라서 리사이즈 허용)
def _display_bgr(rgb: np.ndarray) -> np.ndarray:
    h, w = rgb.shape[:2]
    s = min(1.0, DISPLAY_MAX_SIDE / max(h, w))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    if s < 1.0:
        bgr = cv2.resize(bgr, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_AREA)
    return bgr


# 이미지 왼쪽 위에 "MOCK" 글자 찍기
def _stamp_mock(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    scale = max(0.5, w / 640)
    thick = max(1, int(2 * scale))
    cv2.putText(img, "MOCK", (int(10 * scale), int(40 * scale)), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thick + 3, cv2.LINE_AA)
    cv2.putText(img, "MOCK", (int(10 * scale), int(40 * scale)), cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), thick, cv2.LINE_AA)
    return img


# 가짜 Grad-CAM: 가운데쯤 둥근 히트맵을 원본 위에 겹침
def _write_mock_gradcam(rgb: np.ndarray, out: Path) -> None:
    base = _display_bgr(rgb)
    h, w = base.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy, sx, sy = w * 0.55, h * 0.45, w * 0.25, h * 0.25
    heat = np.exp(-(((xx - cx) / sx) ** 2 + ((yy - cy) / sy) ** 2) / 2)
    heat_u8 = (heat / heat.max() * 255).astype(np.uint8)
    overlay = cv2.addWeighted(base, 0.55, cv2.applyColorMap(heat_u8, cv2.COLORMAP_JET), 0.45, 0)
    cv2.imwrite(str(out), _stamp_mock(overlay))


# 가짜 ELA: 윤곽선을 강조한 흑백 이미지 (실제 ELA 아님)
def _write_mock_ela(rgb: np.ndarray, out: Path) -> None:
    gray = cv2.cvtColor(_display_bgr(rgb), cv2.COLOR_BGR2GRAY)
    edges = cv2.convertScaleAbs(cv2.Laplacian(gray, cv2.CV_16S, ksize=3), alpha=3.0)
    cv2.imwrite(str(out), _stamp_mock(cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)))


# 명세서 예시 JSON 의 sample_* 이미지 주소가 실제로 열리도록 샘플 생성
def ensure_sample_artifacts() -> None:
    orig = RESULTS_DIR / "sample_orig.jpg"
    if orig.exists():
        return
    h, w = 480, 640
    yy, xx = np.mgrid[0:h, 0:w]
    rgb = np.stack([(xx * 255 // w), (yy * 255 // h), np.full_like(xx, 160)], axis=-1).astype(np.uint8)
    cv2.imwrite(str(orig), _stamp_mock(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)))
    _write_mock_gradcam(rgb, RESULTS_DIR / "sample_gradcam.png")
    _write_mock_ela(rgb, RESULTS_DIR / "sample_ela.png")
