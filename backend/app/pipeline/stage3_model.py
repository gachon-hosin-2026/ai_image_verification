# Stage 3 — 딥러닝 추론 + Grad-CAM 히트맵 코드 (뼈대: AI 팀이 채울 부분)
# 1. 224x224 텐서를 ONNX 모델에 넣어 "실사일 확률"을 구함
# 2. 모델이 어디를 보고 판단했는지 히트맵(Grad-CAM)으로 저장함
# 3. 모델은 서버 시작 때 load_model() 로 한 번만 불러옴. 요청마다 불러오면 매우 느려짐
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class ModelResult:
    dl_human_prob: float     # 0~1, 높을수록 실사
    dl_delta: int            # breakdown 점수
    dl_detail: str           # 한국어 설명
    gradcam_image_path: Path


# 모델 불러오기 (TODO: 구현 필요)
# 1. HF Spaces 무료 티어는 CPU 만 있으므로 CPUExecutionProvider 사용
# 2. 예시
#    import onnxruntime as ort
#    return ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
def load_model(model_path: Path) -> Any:
    raise NotImplementedError("Stage 3 모델 로더가 아직 구현되지 않았습니다.")


# 추론 + 히트맵 저장 (TODO: 구현 필요)
# 1. 입력: session(load_model 결과), model_tensor(1,3,224,224), original_rgb(히트맵 겹칠 원본), gradcam_out_path
# 2. 히트맵을 원본 위에 겹쳐서 gradcam_out_path 에 저장 (표시용이라 원본을 줄여도 됨)
# 3. ⚠️ ONNX Runtime 은 기본적으로 gradient(역전파)를 못 구함. 그래서 Grad-CAM 을 하려면 미리 정해야 함
#    - 방법 A: PyTorch 에서 CAM 출력까지 포함해서 ONNX 로 export
#    - 방법 B: 마지막 conv feature map 을 추가 출력으로 export → CAM/Score-CAM 계산
def run_model(
    session: Any,
    model_tensor: np.ndarray,
    original_rgb: np.ndarray,
    gradcam_out_path: Path,
) -> ModelResult:
    raise NotImplementedError("Stage 3 모델 추론이 아직 구현되지 않았습니다.")
