# DB 연결 코드 (SQLAlchemy)
# 1. DATABASE_URL 이 비어 있으면 SQLite(app.db 파일) 사용. 그래서 설치 없이 바로 테스트 가능
# 2. DATABASE_URL 만 PostgreSQL 주소로 바꾸면 코드 수정 없이 DB 전환됨
# 3. 새 컬럼이 생기면 기존 DB 파일에도 자동으로 추가함(_add_missing_columns). 그래서 app.db 를 지우지 않아도 됨
from collections.abc import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

_url = get_settings().database_url
# SQLite 는 여러 스레드에서 접근하므로 같은 스레드 제한을 꺼야 함
_connect_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}

engine = create_engine(_url, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# 서버 시작 시 테이블이 없으면 생성
def init_db() -> None:
    from app.db import models  # noqa: F401  (테이블 등록용 import)

    Base.metadata.create_all(bind=engine)
    _add_missing_columns()


# 나중에 추가된 컬럼을 예전 DB 에 붙여주는 간단한 마이그레이션
# 1. create_all 은 "없는 테이블"만 만들고, 이미 있는 테이블에 컬럼을 추가하지는 않음
# 2. 그래서 아래 목록의 컬럼이 없으면 ALTER TABLE 로 추가함 (기존 기록은 기본값으로 채워짐)
# 3. 컬럼을 새로 만들면 이 목록에 한 줄 추가하세요
_LATER_COLUMNS = {
    "analyses": {"train_consent": ("BOOLEAN DEFAULT 0", "BOOLEAN DEFAULT FALSE")},  # (SQLite, PostgreSQL)
}


def _add_missing_columns(eng=None) -> None:
    eng = eng or engine
    insp = inspect(eng)
    is_sqlite = eng.dialect.name == "sqlite"
    with eng.begin() as conn:
        for table, cols in _LATER_COLUMNS.items():
            existing = {c["name"] for c in insp.get_columns(table)}
            for name, (sqlite_type, pg_type) in cols.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sqlite_type if is_sqlite else pg_type}"))


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
