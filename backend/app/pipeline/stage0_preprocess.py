# Stage 0 — 이미지 전처리 코드 (동작하는 구현)
# 1. 파일 헤더 검사 → 이미지 디코딩 → pHash/SHA-256 계산
# 2. 이미지를 두 갈래로 나눔(Dual-Path)
#    - original_rgb : 크기·화질을 그대로 둔 원본 → Stage 1·2(메타데이터·포렌식)에서 사용
#    - model_tensor : 224x224 로 줄인 텐서 → Stage 3(딥러닝)에서 사용
#    그래서 리사이즈 때문에 FFT·ELA 흔적이 사라지는 문제를 막음
# 3. URL 입력은 안전한 스크래퍼로 이미지를 받아온 뒤 같은 과정을 거침
from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx
import imagehash
import numpy as np
from PIL import Image, UnidentifiedImageError

from app.core.security import SecurityError, require_allowed_image, too_large_message, validate_public_url

MODEL_INPUT_SIZE = (224, 224)
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
MAX_PIXELS = 60_000_000  # 약 60MP 초과 이미지 거부 (압축 폭탄 방지)
MAX_HTML_BYTES = 5 * 1024 * 1024
MAX_REDIRECTS = 5
USER_AGENT = "Mozilla/5.0 (compatible; AuthenticityChecker/1.0; +university-project)"

Image.MAX_IMAGE_PIXELS = MAX_PIXELS

_PIL_FORMAT_TO_MIME = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
_MIME_TO_EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


# 전처리 결과 묶음 (다음 Stage 들이 여기서 필요한 값을 꺼내 씀)
@dataclass
class PreprocessResult:
    raw_bytes: bytes            # 업로드 원본 바이트 그대로 (ELA·EXIF 분석용)
    mime: str
    ext: str
    original_rgb: np.ndarray    # (H, W, 3) uint8 — 리사이즈 금지
    model_tensor: np.ndarray    # (1, 3, 224, 224) float32 — 딥러닝용
    width: int
    height: int
    sha256: str
    phash: str
    exif_bytes: bytes | None
    source_url: str | None = None


# 이미지 바이트 → PreprocessResult
# 1. 헤더 검사 후 PIL 로 디코딩. 깨진 파일·너무 큰 해상도는 400
# 2. 헤더 형식과 실제 디코딩 형식이 다르면 400 (위장 파일 차단)
# 3. EXIF 회전도 적용하지 않음. 그래서 포렌식용 픽셀이 원본 그대로 유지됨
def preprocess_bytes(raw: bytes, source_url: str | None = None) -> PreprocessResult:
    mime = require_allowed_image(raw)

    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Image.DecompressionBombError as e:
        raise SecurityError("이미지 해상도가 너무 큽니다.") from e
    except (UnidentifiedImageError, OSError, SyntaxError) as e:
        raise SecurityError("이미지 파일이 손상되었거나 읽을 수 없습니다.") from e

    if _PIL_FORMAT_TO_MIME.get(img.format or "") != mime:
        raise SecurityError("파일 헤더와 실제 이미지 형식이 일치하지 않습니다.")

    exif_bytes = img.info.get("exif")
    rgb_img = img.convert("RGB")
    original_rgb = np.asarray(rgb_img, dtype=np.uint8).copy()
    height, width = original_rgb.shape[:2]

    return PreprocessResult(
        raw_bytes=raw,
        mime=mime,
        ext=_MIME_TO_EXT[mime],
        original_rgb=original_rgb,
        model_tensor=_to_model_tensor(rgb_img),
        width=width,
        height=height,
        sha256=hashlib.sha256(raw).hexdigest(),
        phash=str(imagehash.phash(rgb_img)),
        exif_bytes=exif_bytes,
        source_url=source_url,
    )


# 딥러닝용 텐서 만들기
# 1. 224x224 리사이즈 → 0~1 정규화 → ImageNet 평균/표준편차 정규화 → (1, 3, H, W)
# 2. 원본 배열과 메모리를 공유하지 않는 별도 사본. 그래서 원본이 절대 바뀌지 않음
def _to_model_tensor(rgb_img: Image.Image) -> np.ndarray:
    resized = rgb_img.resize(MODEL_INPUT_SIZE, Image.Resampling.BICUBIC)
    arr = np.asarray(resized, dtype=np.float32) / 255.0
    arr = (arr - IMAGENET_MEAN) / IMAGENET_STD
    return np.ascontiguousarray(arr.transpose(2, 0, 1)[None, ...], dtype=np.float32)


# 웹페이지 HTML 에서 대표 이미지 주소 찾기
# 1. og:image → twitter:image → 첫 번째 <img> 순서로 찾음
class _ImageMetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.og: str | None = None
        self.twitter: str | None = None
        self.first_img: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            if key in ("og:image", "og:image:url", "og:image:secure_url") and not self.og:
                self.og = a.get("content") or None
            elif key in ("twitter:image", "twitter:image:src") and not self.twitter:
                self.twitter = a.get("content") or None
        elif tag == "img" and not self.first_img:
            self.first_img = a.get("src") or a.get("data-src") or None

    @property
    def best(self) -> str | None:
        return self.og or self.twitter or self.first_img


# 안전하게 URL 내용 받아오기
# 1. 리다이렉트를 자동으로 따라가지 않고 직접 따라감. 그래서 매번 SSRF 검사를 다시 할 수 있음
# 2. 받는 도중 max_bytes 를 넘으면 413
def _safe_get(client: httpx.Client, url: str, max_bytes: int) -> tuple[bytes, str, str]:
    for _ in range(MAX_REDIRECTS + 1):
        validate_public_url(url)
        with client.stream("GET", url) as resp:
            if resp.is_redirect:
                url = urljoin(url, resp.headers.get("location", ""))
                continue
            if resp.status_code >= 400:
                raise SecurityError(f"URL에서 콘텐츠를 가져오지 못했습니다. (HTTP {resp.status_code})")
            buf = bytearray()
            for chunk in resp.iter_bytes():
                buf.extend(chunk)
                if len(buf) > max_bytes:
                    raise SecurityError(too_large_message(max_bytes), status_code=413)
            return bytes(buf), resp.headers.get("content-type", "").lower(), str(resp.url)
    raise SecurityError("리다이렉트 횟수가 너무 많습니다.")


# 뉴스/커뮤니티 URL 또는 이미지 직링크에서 이미지 가져오기
# 1. HTML 이면 대표 이미지 주소를 찾아서 한 번 더 요청
# 2. 이미지면 바로 사용
# 3. 반환: (이미지 바이트, 실제 이미지 URL)
def fetch_image_from_url(url: str, max_bytes: int, timeout: float) -> tuple[bytes, str]:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,image/avif,image/webp,image/*,*/*;q=0.8"}
    try:
        with httpx.Client(follow_redirects=False, timeout=timeout, headers=headers) as client:
            body, ctype, final_url = _safe_get(client, url, max(max_bytes, MAX_HTML_BYTES))
            if "html" in ctype:
                parser = _ImageMetaParser()
                parser.feed(body.decode("utf-8", errors="ignore"))
                if not parser.best:
                    raise SecurityError("페이지에서 분석할 이미지를 찾지 못했습니다.")
                img_url = urljoin(final_url, parser.best)
                body, _, final_url = _safe_get(client, img_url, max_bytes)
            elif len(body) > max_bytes:
                raise SecurityError(too_large_message(max_bytes), status_code=413)
    except httpx.TimeoutException as e:
        raise SecurityError("URL 응답 시간이 초과되었습니다.") from e
    except httpx.HTTPError as e:
        raise SecurityError("URL에 연결하지 못했습니다.") from e

    require_allowed_image(body)
    return body, final_url


# SNS 재압축 흉내내기 (재압축 스트레스 테스트용)
# 1. 메모리 안에서 50% 축소 → JPEG 품질 75 로 저장
# 2. EXIF 를 넣지 않음. 그래서 카카오톡·인스타처럼 메타데이터가 사라진 상태가 됨
def simulate_sns_recompression(raw: bytes, scale: float = 0.5, quality: int = 75) -> bytes:
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    new_size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    img = img.resize(new_size, Image.Resampling.BILINEAR)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=quality)
    return out.getvalue()
