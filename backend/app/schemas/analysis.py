# API 요청/응답 형식을 정의하는 코드 (명세서 Section 5 고정 계약)
# 1. 여기 적힌 필드 이름·타입대로만 JSON 이 나감. 그래서 프론트엔드는 이 형식만 믿고 개발하면 됨
# 2. 필드를 바꾸면 프론트엔드가 깨지므로 팀 합의 없이 수정 금지
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


# 4등급 (점수 구간)
class Grade(str, Enum):
    SAFE_LIKELY_REAL = "SAFE_LIKELY_REAL"                              # 80–100 실사 유력 / 안전
    CAUTION_EDITED_OR_RECOMPRESSED = "CAUTION_EDITED_OR_RECOMPRESSED"  # 55–79 편집·재압축 의심 (Gray Zone)
    WARNING_AI_SUSPECTED = "WARNING_AI_SUSPECTED"                      # 30–54 AI 생성 의심 / 경고
    DANGER_HIGHLY_LIKELY_AI = "DANGER_HIGHLY_LIKELY_AI"                # 0–29 AI 생성 매우 유력 / 위험


# 조작 범위
class ManipulationScope(str, Enum):
    LIKELY_AUTHENTIC = "LIKELY_AUTHENTIC"            # 실사 유력
    LOCAL_EDIT_SUSPECTED = "LOCAL_EDIT_SUSPECTED"    # 부분 보정·합성 의심
    GLOBAL_AI_GENERATED = "GLOBAL_AI_GENERATED"      # AI 전면 생성 의심


class UserLabel(str, Enum):
    REAL = "REAL"
    AI = "AI"
    CORRECT = "CORRECT"


# ── 응답 ──
class Metrics(BaseModel):
    dl_human_prob: float
    fft_hf_ratio: float
    fft_slope: float
    ela_mean: float
    ela_std: float
    ela_top5_concentration: float
    meta_status_code: int  # 0 = EXIF 없음(중립). 절대 감점하지 않음


class BreakdownItem(BaseModel):
    factor: str   # 한국어
    delta: int    # 점수 기여분 (+/-)
    detail: str   # 한국어


class VisualArtifacts(BaseModel):
    original_url: str
    gradcam_url: str
    ela_url: str


class AnalysisResponse(BaseModel):
    analysis_id: str
    cached: bool
    authenticity_score: int = Field(ge=0, le=100)  # 높을수록 실사, 낮을수록 AI (절대 반전 금지)
    grade: Grade
    manipulation_scope: ManipulationScope
    latency_ms: int
    metrics: Metrics
    breakdown: list[BreakdownItem]
    visual_artifacts: VisualArtifacts


class HealthResponse(BaseModel):
    status: str
    mode: str
    version: str


class RecompressTestResponse(BaseModel):
    analysis_id: str
    original_score: int
    recompressed_score: int
    score_diff: int = Field(description="재압축 점수 - 원본 점수")
    original: AnalysisResponse
    recompressed: AnalysisResponse


class FeedbackResponse(BaseModel):
    feedback_id: int
    analysis_id: str
    status: str


# ── 요청 ──
class AnalyzeUrlRequest(BaseModel):
    url: HttpUrl
    train_consent: bool = False  # 학습 데이터 활용 동의 (선택)


class RecompressTestRequest(BaseModel):
    analysis_id: str


class FeedbackRequest(BaseModel):
    analysis_id: str
    user_label: UserLabel
    comment: str | None = Field(default=None, max_length=2000)
