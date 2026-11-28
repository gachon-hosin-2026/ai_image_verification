# Stage 1 — EXIF·C2PA 메타데이터 분석 코드 (뼈대: AI/포렌식 팀이 채울 부분)
# 1. 원본 파일에서 카메라 정보·편집 프로그램·C2PA 서명을 읽음
# 2. 결과를 status_code 와 점수(score_delta)로 바꿔서 Stage 4·5 로 넘김
# 3. ⚠️ EXIF 가 없으면 무조건 중립(0점) 처리. 카카오톡·인스타는 EXIF 를 지우기 때문에 감점하면 진짜 사진이 억울해짐
from __future__ import annotations

from dataclasses import dataclass, field

# meta_status_code 규칙 (팀 합의 후 확정)
META_NEUTRAL_MISSING = 0       # EXIF/C2PA 없음 → 중립 (감점 금지)
META_CAMERA_CONSISTENT = 1     # 카메라 정보가 일관됨 → 가점 가능
META_EDITING_SOFTWARE = 2      # Photoshop 등 편집 프로그램 흔적
META_AI_TOOL_SIGNATURE = 3     # 생성형 AI 도구 서명 있음
META_C2PA_VERIFIED_REAL = 4    # C2PA 로 실촬영 검증됨


@dataclass
class MetadataResult:
    status_code: int = META_NEUTRAL_MISSING
    score_delta: int = 0                       # breakdown 에 표시될 점수
    detail: str = "정보 없음 (SNS 재압축 가능성으로 중립 처리)"
    camera_make: str | None = None
    camera_model: str | None = None
    software: str | None = None
    has_c2pa: bool = False
    raw_tags: dict[str, str] = field(default_factory=dict)


# 메타데이터 분석 (TODO: 구현 필요)
# 1. 입력: raw_bytes(원본 파일), exif_bytes(Stage 0 에서 뽑은 EXIF, 없으면 None), mime
# 2. EXIF 없음 → 바로 중립 결과 반환 (이 분기는 지우지 말 것)
# 3. 구현 힌트
#    - PIL.Image.Exif().load(exif_bytes) 로 Make(271) / Model(272) / Software(305) 태그 확인
#    - C2PA 는 c2pa-python 패키지 검토 (무료·로컬 실행)
def analyze_metadata(raw_bytes: bytes, exif_bytes: bytes | None, mime: str) -> MetadataResult:
    if not exif_bytes:
        return MetadataResult()
    raise NotImplementedError("Stage 1 메타데이터 분석이 아직 구현되지 않았습니다.")
