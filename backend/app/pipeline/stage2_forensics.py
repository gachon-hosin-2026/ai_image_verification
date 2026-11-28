# Stage 2 — FFT 주파수 + ELA 압축 잔차 분석 코드 (뼈대: 포렌식 팀이 채울 부분)
# 1. 원본 픽셀로 고주파 패턴(FFT)과 재압축 차이(ELA)를 계산함
# 2. 수치는 Stage 4 점수 계산에, ELA 이미지는 화면 표시에 쓰임
# 3. ⚠️ 반드시 리사이즈 안 한 원본(original_rgb / raw_bytes)만 사용. 줄이면 흔적이 사라짐
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class ForensicsResult:
    fft_hf_ratio: float            # 고주파 에너지 비율
    fft_slope: float               # 주파수 스펙트럼 기울기 (log-log)
    ela_mean: float
    ela_std: float
    ela_top5_concentration: float  # 잔차 상위 5% 가 몰린 정도 → 부분 편집 판단에 사용
    fft_delta: int                 # breakdown 점수
    fft_detail: str                # 한국어 설명
    ela_delta: int
    ela_detail: str
    ela_image_path: Path           # 저장된 ELA 이미지 경로


# 포렌식 분석 (TODO: 구현 필요)
# 1. 입력: original_rgb(원본 RGB), raw_bytes(원본 파일), mime, ela_out_path(ELA 이미지 저장 위치)
# 2. FFT: 흑백 변환 → np.fft.fft2 → fftshift → 원형 평균 → np.polyfit 으로 기울기
# 3. ELA: 원본을 JPEG 품질 90 으로 다시 저장 → |원본 - 재저장| → 밝기 증폭 → cv2.imwrite
# 4. 큰 이미지는 FFT 를 가운데 1024x1024 로 '잘라서' 계산 (리사이즈는 금지)
# 5. PNG/WEBP(무손실)는 ELA 해석이 JPEG 과 다르니 분기 처리 권장
def analyze_forensics(
    original_rgb: np.ndarray,
    raw_bytes: bytes,
    mime: str,
    ela_out_path: Path,
) -> ForensicsResult:
    raise NotImplementedError("Stage 2 포렌식 분석이 아직 구현되지 않았습니다.")
