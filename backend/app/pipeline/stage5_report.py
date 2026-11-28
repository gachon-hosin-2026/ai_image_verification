# Stage 5 — 조작 범위 판정 + 점수 설명(breakdown) 코드
# 1. 전체가 AI 생성인지(GLOBAL) / 일부만 편집인지(LOCAL) / 실사인지 판정함 (뼈대: AI/포렌식 팀이 채울 부분)
# 2. 각 단계 점수를 신용점수처럼 항목별로 정리함(이미 구현). 그래서 사용자가 "왜 이 점수인지" 알 수 있음
from __future__ import annotations

from dataclasses import dataclass

from app.pipeline.stage1_metadata import MetadataResult
from app.pipeline.stage2_forensics import ForensicsResult
from app.pipeline.stage3_model import ModelResult
from app.pipeline.stage4_ensemble import EnsembleResult
from app.schemas.analysis import BreakdownItem, ManipulationScope


@dataclass
class ReportResult:
    manipulation_scope: ManipulationScope
    breakdown: list[BreakdownItem]


# breakdown 만들기 (항목 순서·이름은 API 계약 예시와 동일하게 유지)
def build_breakdown(model: ModelResult, forensics: ForensicsResult, meta: MetadataResult) -> list[BreakdownItem]:
    return [
        BreakdownItem(factor="딥러닝 시각 패턴 분석", delta=model.dl_delta, detail=model.dl_detail),
        BreakdownItem(factor="FFT 고주파 스펙트럼", delta=forensics.fft_delta, detail=forensics.fft_detail),
        BreakdownItem(factor="ELA 압축 잔차", delta=forensics.ela_delta, detail=forensics.ela_detail),
        BreakdownItem(factor="EXIF 메타데이터", delta=meta.score_delta, detail=meta.detail),
    ]


# 조작 범위 판정 (TODO: 구현 필요, 기준값은 팀이 실험으로 결정)
# 1. 점수가 높으면 → LIKELY_AUTHENTIC
# 2. ELA 잔차가 한 곳에 몰려 있으면(ela_top5_concentration 높음) → LOCAL_EDIT_SUSPECTED
# 3. 딥러닝이 AI 로 보고 잔차가 고르게 퍼져 있으면 → GLOBAL_AI_GENERATED
def decide_scope(ensemble: EnsembleResult, model: ModelResult, forensics: ForensicsResult) -> ManipulationScope:
    raise NotImplementedError("Stage 5 조작 범위 판정이 아직 구현되지 않았습니다.")


def build_report(
    ensemble: EnsembleResult,
    model: ModelResult,
    forensics: ForensicsResult,
    meta: MetadataResult,
) -> ReportResult:
    return ReportResult(
        manipulation_scope=decide_scope(ensemble, model, forensics),
        breakdown=build_breakdown(model, forensics, meta),
    )
