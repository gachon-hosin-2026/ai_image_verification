# Hugging Face Spaces (Docker SDK) 호환 Dockerfile
# Spaces 는 컨테이너를 UID 1000 사용자로 실행하고, 7860 포트로 트래픽을 보냅니다.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860 \
    USE_MOCK_PIPELINE=true

# OpenCV(headless) 런타임에 필요한 최소 시스템 라이브러리
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# HF Spaces 권장: UID 1000 비루트 사용자
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH
WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install --user --upgrade pip && pip install --user -r requirements.txt

COPY --chown=user . .
RUN mkdir -p app/static/results models

EXPOSE 7860
# PORT 환경 변수로 포트 결정 (Spaces 기본 7860)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
