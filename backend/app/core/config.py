# 서버 설정을 불러오는 코드
# 1. .env 파일(없으면 OS 환경 변수)에서 값을 읽음. 그래서 .env 만 고치면 서버 동작이 바뀜
# 2. 다른 파일들은 get_settings() 로 이 설정을 가져다 씀
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# 자주 쓰는 폴더 경로
# 1. BASE_DIR = backend 폴더. 실행 위치와 상관없이 항상 같은 경로를 가리킴
BASE_DIR = Path(__file__).resolve().parents[2]
APP_DIR = BASE_DIR / "app"
RESULTS_DIR = APP_DIR / "static" / "results"
MODELS_DIR = BASE_DIR / "models"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    APP_VERSION: str = "1.0.0"
    PORT: int = 8000
    USE_MOCK_PIPELINE: bool = True
    MOCK_SCORE_MODE: Literal["fixed", "hash"] = "fixed"

    # 비어 있으면 backend/app.db (SQLite) 사용
    DATABASE_URL: str = ""

    # "*" 또는 쉼표로 구분한 주소 목록
    ALLOW_ORIGINS: str = "*"

    CACHE_MATCH: Literal["phash", "sha256", "off"] = "phash"

    # 보안
    # 1. ACCESS_KEY: 비어 있으면 키 검사 안 함. 외부 공개(터널) 때는 반드시 설정
    # 2. RATE_LIMIT_PER_MIN: 같은 IP 의 분석 요청(POST) 분당 최대 횟수. 0 이면 제한 없음
    ACCESS_KEY: str = ""
    RATE_LIMIT_PER_MIN: int = 20

    MAX_UPLOAD_MB: int = 20
    URL_FETCH_TIMEOUT_SEC: float = 10.0

    ONNX_MODEL_FILE: str = "detector.onnx"
    META_CLASSIFIER_FILE: str = "meta_xgb.joblib"

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL or f"sqlite:///{(BASE_DIR / 'app.db').as_posix()}"

    @property
    def allow_origins_list(self) -> list[str]:
        items = [o.strip() for o in self.ALLOW_ORIGINS.split(",") if o.strip()]
        return items or ["*"]

    @property
    def auth_enabled(self) -> bool:
        return bool(self.ACCESS_KEY)

    @property
    def mode(self) -> str:
        return "mock" if self.USE_MOCK_PIPELINE else "production"


# 설정 객체를 한 번만 만들어서 재사용
@lru_cache
def get_settings() -> Settings:
    return Settings()
