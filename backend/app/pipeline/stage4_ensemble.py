# Stage 4 — 최종 점수(0~100) + 4등급 계산 코드
# 1. Stage 1~3 수치를 XGBoost 에 넣어 실사 확률을 구하고 0~100 점으로 바꿈 (뼈대: AI 팀이 채울 부분)
# 2. 점수 → 등급 변환(score_to_grade)은 API 계약으로 고정이라 이미 구현됨
# 3. ⚠️ 점수 방향 절대 반전 금지: 높을수록 실사, 낮을수록 AI
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.schemas.analysis import Grade

# XGBoost 입력 순서 (학습 코드와 반드시 같아야 함. 다르면 점수가 엉뚱하게 나옴)
FEATURE_ORDER: tuple[str, ...] = (
    "dl_human_prob",
    "fft_hf_ratio",
    "fft_slope",
    "ela_mean",
    "ela_std",
    "ela_top5_concentration",
    "meta_status_code",
)


@dataclass
class EnsembleResult:
    authenticity_score: int  # 0~100
    grade: Grade


# 점수 → 4등급 (80 / 55 / 30 경계)
def score_to_grade(score: int) -> Grade:
    if score >= 80:
        return Grade.SAFE_LIKELY_REAL
    if score >= 55:
        return Grade.CAUTION_EDITED_OR_RECOMPRESSED
    if score >= 30:
        return Grade.WARNING_AI_SUSPECTED
    return Grade.DANGER_HIGHLY_LIKELY_AI


# XGBoost 모델 불러오기 (TODO: 구현 필요)
# 1. 예시: return joblib.load(path)
def load_meta_classifier(path: Path) -> Any:
    raise NotImplementedError("Stage 4 메타 분류기 로더가 아직 구현되지 않았습니다.")


# 점수 계산 (TODO: 구현 필요)
# 1. features dict 를 FEATURE_ORDER 순서로 배열로 만듦
# 2. predict_proba 로 실사 확률(클래스 1 = 실사 로 학습할 것) → ×100 → 반올림
# 3. 예시
#    x = np.array([[features[k] for k in FEATURE_ORDER]], dtype=np.float32)
#    p_real = float(classifier.predict_proba(x)[0, 1])
#    score = int(round(p_real * 100))
#    return EnsembleResult(score, score_to_grade(score))
def compute_score(features: dict[str, float], classifier: Any) -> EnsembleResult:
    raise NotImplementedError("Stage 4 앙상블 점수 계산이 아직 구현되지 않았습니다.")
