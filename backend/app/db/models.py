# DB 테이블 정의 코드
# 1. analyses: 분석 1건마다 1줄 저장 (점수, 원본 경로, 응답 JSON 전체). 그래서 캐시·재압축 테스트에 재사용
# 2. feedbacks: 사용자 피드백 저장. 나중에 Active Learning 학습 데이터로 사용
# 3. train_consent: 업로드한 사람이 학습 데이터 활용에 동의했는지. 학습 데이터 내보낼 때 이 값으로 거름
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    mode: Mapped[str] = mapped_column(String(16))                   # mock / production
    source_type: Mapped[str] = mapped_column(String(16))            # upload / url / recompress
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # 재압축 테스트의 원본 ID

    mime: Mapped[str] = mapped_column(String(32))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    phash: Mapped[str] = mapped_column(String(64), index=True)
    original_path: Mapped[str] = mapped_column(Text)                # 원본 파일 경로 (무손실)
    train_consent: Mapped[bool] = mapped_column(Boolean, default=False)  # 학습 데이터 활용 동의

    authenticity_score: Mapped[int] = mapped_column(Integer)
    grade: Mapped[str] = mapped_column(String(48))
    manipulation_scope: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[int] = mapped_column(Integer)
    result_json: Mapped[dict] = mapped_column(JSON)                 # 응답 JSON 전체

    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="analysis")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), index=True)
    user_label: Mapped[str] = mapped_column(String(16))             # REAL / AI / CORRECT
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis: Mapped[Analysis] = relationship(back_populates="feedbacks")
