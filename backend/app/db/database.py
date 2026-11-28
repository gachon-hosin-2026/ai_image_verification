# DB 연결 코드 (SQLAlchemy)
# 1. DATABASE_URL 이 비어 있으면 SQLite(app.db 파일) 사용. 그래서 설치 없이 바로 테스트 가능
# 2. DATABASE_URL 만 PostgreSQL 주소로 바꾸면 코드 수정 없이 DB 전환됨
from collections.abc import Iterator

from sqlalchemy import create_engine
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


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
