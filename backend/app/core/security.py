# 보안 검사 코드 (파일 형식, 용량, 위험한 URL 차단)
# 1. 업로드 파일의 실제 헤더를 보고 JPEG/PNG/WEBP 인지 확인함. 그래서 확장자만 바꾼 가짜 파일은 400
# 2. 업로드를 조금씩 읽다가 20MB 를 넘으면 바로 중단함. 그래서 큰 파일로 서버 메모리를 채울 수 없음
# 3. URL 이 내부망·사설 IP 를 가리키면 거부함(SSRF 방지). 그래서 서버 내부 자원에 접근 불가
# 4. 접근 키 검사 + IP 별 요청 횟수 제한. 그래서 주소를 알아낸 외부인·봇이 분석 API 를 마구 쓸 수 없음
from __future__ import annotations

import ipaddress
import secrets
import socket
import time
from collections import defaultdict, deque
from urllib.parse import urlsplit

from fastapi import Depends, HTTPException, Request, UploadFile, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings

ALLOWED_MIME = ("image/jpeg", "image/png", "image/webp")
ALLOWED_PORTS = {80, 443}  # 일반 웹 포트만 허용


# 사용자에게 그대로 보여줄 한국어 메시지를 담는 오류
class SecurityError(ValueError):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# 파일 앞부분(Magic Bytes)으로 이미지 형식 판별
# 1. JPEG = FF D8 FF / PNG = 89 50 4E 47 ... / WEBP = RIFF....WEBP
# 2. 셋 다 아니면 None 반환
def detect_image_mime(data: bytes) -> str | None:
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


# 허용된 이미지가 아니면 400 오류
def require_allowed_image(data: bytes) -> str:
    mime = detect_image_mime(data)
    if mime not in ALLOWED_MIME:
        raise SecurityError("지원하지 않는 파일 형식입니다. JPEG, PNG, WEBP 이미지만 업로드할 수 있습니다.")
    return mime


def too_large_message(max_bytes: int) -> str:
    return f"파일 크기가 너무 큽니다. 최대 {max_bytes // (1024 * 1024)}MB까지 업로드할 수 있습니다."


# 업로드 파일을 1MB 씩 읽으며 용량 확인
# 1. 누적 크기가 max_bytes 를 넘는 순간 413 오류
# 2. 빈 파일이면 400 오류
async def read_upload_limited(file: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(1024 * 1024):
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, too_large_message(max_bytes))
        chunks.append(chunk)
    if total == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "빈 파일입니다.")
    return b"".join(chunks)


# 공인 IP 인지 확인
# 1. ::ffff:127.0.0.1 같은 IPv6 우회 표기를 IPv4 로 바꿔서 검사
# 2. is_global 이 사설(10/172.16/192.168), 루프백(127), 링크로컬(169.254) 등을 모두 걸러줌
def _is_public_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


# URL 이 안전한 외부 주소인지 검사
# 1. http/https, 포트 80/443, 아이디·비밀번호 없는 URL 만 통과
# 2. 도메인을 IP 로 바꿔서 하나라도 내부 IP 면 거부
# 3. 한계: 검사 후 DNS 응답이 바뀌는 공격(DNS 리바인딩)은 완벽히 못 막음. 그래서 리다이렉트마다 다시 검사함
def validate_public_url(url: str) -> str:
    try:
        parts = urlsplit(url)
    except ValueError as e:
        raise SecurityError("올바르지 않은 URL 형식입니다.") from e

    if parts.scheme not in ("http", "https"):
        raise SecurityError("http 또는 https URL만 분석할 수 있습니다.")
    host = parts.hostname
    if not host:
        raise SecurityError("URL에 호스트가 없습니다.")
    if parts.username or parts.password:
        raise SecurityError("인증 정보가 포함된 URL은 허용되지 않습니다.")
    try:
        port = parts.port or (443 if parts.scheme == "https" else 80)
    except ValueError as e:
        raise SecurityError("올바르지 않은 포트 번호입니다.") from e
    if port not in ALLOWED_PORTS:
        raise SecurityError("표준 포트(80, 443)의 URL만 허용됩니다.")

    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise SecurityError("URL의 도메인을 찾을 수 없습니다.") from e

    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if not _is_public_ip(ip):
            raise SecurityError("내부망·사설 IP를 가리키는 URL은 보안상 허용되지 않습니다.")
    return url


# ── 접근 키 ──────────────────────────────────────────────────
# 팀원만 분석 API 를 쓰게 하는 간단한 비밀번호
# 1. .env 의 ACCESS_KEY 가 비어 있으면 검사 안 함 (로컬 개발용)
# 2. 값이 있으면 요청 헤더 X-Access-Key 가 같아야 통과. 틀리면 401
# 3. compare_digest 로 비교해서 글자를 하나씩 맞혀보는 공격(타이밍 공격)을 막음

ACCESS_KEY_HEADER = "X-Access-Key"
# auto_error=False: 헤더가 없어도 FastAPI 기본 오류 대신 아래 한국어 오류를 쓰기 위함
# /docs 화면 오른쪽 위 'Authorize' 버튼에 키를 넣으면 테스트 요청에도 자동으로 붙음
_api_key_header = APIKeyHeader(name=ACCESS_KEY_HEADER, auto_error=False, description="팀에서 받은 접근 키")


def key_matches(given: str | None, expected: str) -> bool:
    return bool(given) and secrets.compare_digest(given.encode(), expected.encode())


def require_access_key(given: str | None = Depends(_api_key_header)) -> None:
    expected = get_settings().ACCESS_KEY
    if expected and not key_matches(given, expected):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "접근 키가 없거나 올바르지 않습니다. 팀에서 받은 접근 키를 입력하세요.",
        )


# ── 요청 횟수 제한 ───────────────────────────────────────────
# 같은 IP 가 1분 동안 보낼 수 있는 분석 요청(POST) 수 제한
# 1. IP 마다 최근 60초 요청 시각을 기록하고, 한도를 넘으면 429 + 몇 초 뒤 다시 하라고 알려줌
# 2. 메모리에만 저장. 그래서 서버를 재시작하면 기록이 초기화됨 (1대 서버 기준으로 충분)
class RateLimiter:
    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> int:
        """통과하면 0, 막히면 다시 시도까지 남은 초를 반환."""
        if self.per_minute <= 0:
            return 0
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= self.per_minute:
            return max(1, int(60 - (now - q[0])) + 1)
        q.append(now)
        # 오래된 IP 기록 정리 (메모리 누수 방지)
        if len(self.hits) > 5000:
            for ip in [ip for ip, d in self.hits.items() if not d or now - d[-1] > 60]:
                del self.hits[ip]
        return 0


def client_ip(request: Request) -> str:
    # Tailscale Funnel·로컬 실행에서는 실제 접속 IP 가 그대로 들어옴
    # (X-Forwarded-For 는 누구나 위조할 수 있어서 믿지 않음)
    return request.client.host if request.client else "unknown"
