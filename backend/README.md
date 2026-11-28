# AI 이미지 진위 판별 — 백엔드 서버

점수 방향: **높을수록 실사, 낮을수록 AI 생성** (0–100).
`USE_MOCK_PIPELINE=true` 면 AI 파이프라인 없이 고정 JSON 계약과 플레이스홀더 이미지를 반환합니다.

## 팀 역할별 작업 위치

| 담당 | 수정할 곳 | 건드리지 말 것 |
|---|---|---|
| AI / 포렌식 | `app/pipeline/stage1~5_*.py`, `models/` | `app/api`, `app/main.py`, `app/schemas` |
| 백엔드 | `app/api`, `app/core`, `app/db`, `app/main.py` | — |
| 프론트엔드 | (코드 수정 없음) `/docs` 의 계약대로 호출 | — |

각 stage 파일의 `NotImplementedError` 부분만 채우면 `USE_MOCK_PIPELINE=false` 에서 바로 연결됩니다.
`stage0_preprocess.py` 와 `stage4_ensemble.score_to_grade()` 는 이미 동작하는 구현입니다.

---

## 실행 방법

**가장 쉬운 방법:** 저장소 루트의 `scripts\start-dev.bat` 더블클릭 (개인 개발 서버: 백엔드 8001 + 프론트 3001).
공용 서버 운영은 [docs/server-guide.md](../docs/server-guide.md) 를 보세요.

아래는 스크립트 없이 직접 실행하는 방법입니다.

> 권장 Python: **3.11 ~ 3.14** (Dockerfile 은 3.11)

### 1) 최초 1회 설치

**Windows (cmd)**
```cmd
cd backend
py -3 -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
```

**macOS (터미널)**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2) 접근 키 설정 (최초 1회)

외부에 공개하기 전에 `.env` 의 `ACCESS_KEY` 를 반드시 채우세요. 키는 아래 명령으로 만들 수 있습니다.
```cmd
python -c "import secrets; print(secrets.token_urlsafe(24))"
```
출력된 값을 `.env` 에 `ACCESS_KEY=출력된값` 으로 넣고, **팀원에게만 메신저로 따로** 알려주세요. (GitHub 에 올리지 않기)

### 3) 서버 실행 (터미널 ①)

가상환경을 활성화한 상태에서 (Windows / macOS 동일):
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- `127.0.0.1` 로 켜면 같은 와이파이의 다른 기기는 직접 접속할 수 없고, Tailscale 통로로만 들어옵니다. (학교·카페 와이파이에서 더 안전)
- 확인: http://localhost:8000/health → `{"status":"ok","mode":"mock",...}`
- 시작 로그에 `🔒 접근 키 사용 중` 이 보이면 키가 적용된 것입니다.

### 4) Tailscale Funnel 로 고정 공개 주소 열기 (터미널 ②)

> 공용 서버는 `start-server.bat` 가 프론트(3000)를 Funnel 에 연결하고, 프론트가 `/api` 를 백엔드로 전달합니다.
> 아래는 **백엔드만** 직접 공개할 때의 방법입니다.

최초 1회: `winget install --id Tailscale.Tailscale` 설치 → 트레이 아이콘으로 로그인 → 관리 페이지 DNS 에서 MagicDNS·HTTPS 켜기.

```cmd
tailscale funnel 8000
```
- 출력된 `https://pc이름.tailXXXX.ts.net/` 이 **고정 주소**입니다. 다시 켜도 바뀌지 않습니다.
- 공개를 멈추려면 이 창에서 `Ctrl+C`. **테스트할 때만 켜 두세요.**
- 공개 직후 `/.env`, `/wp-config.php` 같은 요청이 로그에 보이는 건 인터넷 전체를 도는 자동 봇입니다. 전부 404 로 막히니 정상입니다.

### 5) 테스트

- `https://고정주소/docs` → 접근 키 입력 → Swagger 화면 오른쪽 위 **Authorize** 에 같은 키 입력 → `POST /api/v1/analyze/image` → **Try it out**
- curl:
```bash
curl -H "X-Access-Key: 접근키" -F "file=@test.jpg" https://고정주소/api/v1/analyze/image
```

> 프론트엔드 참고: `visual_artifacts.*_url` 은 `/static/results/...` 형태의 **상대 경로**입니다.
> 화면에 표시할 때 API 서버 주소를 앞에 붙이세요. 예: `${API_BASE}${gradcam_url}`

---

## 테스트

PR 을 올리면 GitHub Actions 가 자동으로 실행하지만, 올리기 전에 내 컴퓨터에서 먼저 돌려볼 수 있습니다.
```cmd
pip install -r requirements-dev.txt
pytest
```
API 계약(JSON 형식·등급 구간·EXIF 중립), 접근 키, 파일 형식 검사, SSRF 차단, 요청 횟수 제한을 확인합니다. (`tests/test_api.py`)

---

## 보안 설정 요약

| 항목 | 내용 |
|---|---|
| 접근 키 | `ACCESS_KEY` 가 있으면 `/api/...` 요청에 `X-Access-Key` 헤더 필요 (없거나 틀리면 401) |
| `/docs` 보호 | 키가 있을 때만 API 문서·목록(`/openapi.json`) 공개. `/redoc` 은 꺼짐 |
| 요청 횟수 제한 | 같은 IP 의 분석 요청은 1분에 `RATE_LIMIT_PER_MIN` 번까지 (초과 시 429) |
| 보안 헤더 | `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` |
| 업로드 검사 | 20MB 제한, 실제 파일 헤더 검사, 초고해상도(압축 폭탄) 차단 |
| URL 분석 | 내부망·사설 IP 차단(SSRF), 리다이렉트마다 재검사 |
| 열려 있는 것 | `/`, `/health`, 결과 이미지(`/static/results/추측 불가능한 UUID 파일명`) |

---

## 환경 변수 (`.env`)

| 변수 | 기본값 | 설명 |
|---|---|---|
| `PORT` | 8000 | HF Spaces 에서는 7860 |
| `USE_MOCK_PIPELINE` | true | false 면 실제 stage1~5 + 모델 사용 |
| `MOCK_SCORE_MODE` | fixed | `fixed`=명세 예시 38점 / `hash`=이미지마다 다른 점수(4등급 UI 테스트용) |
| `DATABASE_URL` | (비움 → `backend/app.db`) | PostgreSQL: `postgresql+psycopg://user:pw@host:5432/db` |
| `ALLOW_ORIGINS` | `*` | 운영: `https://your-app.vercel.app` (쉼표로 여러 개) |
| `CACHE_MATCH` | phash | `phash` / `sha256` / `off` |
| `ACCESS_KEY` | (비움 → 검사 안 함) | 외부 공개 전 필수. 팀원에게만 공유 |
| `RATE_LIMIT_PER_MIN` | 20 | 같은 IP 분석 요청 분당 최대 (0 = 제한 없음) |

## API 요약

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/`, `/health` | 상태 확인 |
| POST | `/api/v1/analyze/image` | multipart, 필드명 `file` (JPEG/PNG/WEBP, 20MB 이하) |
| POST | `/api/v1/analyze/url` | `{"url": "..."}` — og:image → twitter:image → 첫 `<img>` 순으로 추출 |
| POST | `/api/v1/analyze/recompress-test` | `{"analysis_id": "..."}` — 50% 축소 + JPEG 75 재압축 후 비교 |
| POST | `/api/v1/feedback` | `{"analysis_id","user_label":"REAL"\|"AI"\|"CORRECT","comment"}` → 201 |

오류 코드: `400` 형식/URL 거부, `401` 접근 키 없음·틀림, `413` 20MB 초과, `429` 요청 너무 많음, `404` 없는 analysis_id, `422` 요청 필드 오류,
`501` stage 미구현, `503` Production 모드인데 모델 미로드.

---

## Step 5. Hugging Face Spaces 배포 (Week 3~4) — ⚠️ 재검토 필요

> 2026년 현재 HF Spaces 는 Docker Space 실행에 유료 플랜이 필요하고, 무료 디스크는 재시작 시 초기화됩니다.
> 학습 데이터를 쌓는 공용 서버는 태연 PC 에서 운영하고, 이 섹션은 회의 후 결정합니다.

1. https://huggingface.co/new-space → **SDK: Docker** → Blank → Hardware: CPU basic(무료)
2. Space 저장소 루트에 이 `backend/` 내용물을 그대로 올리고, Space 의 `README.md` 맨 위에 아래 헤더를 둡니다:
   ```yaml
   ---
   title: AI Image Authenticity
   sdk: docker
   app_port: 7860
   ---
   ```
3. Space **Settings → Variables** 에 `USE_MOCK_PIPELINE`, `ALLOW_ORIGINS`(Vercel 도메인), 필요 시 `DATABASE_URL` 설정
   `ACCESS_KEY` 는 **Secrets** 에 넣으세요 (Variables 는 공개됨)
4. 모델 가중치(`.onnx`, `.joblib`)는 용량이 크므로 **Git LFS** 로 올리세요. (`.gitignore` 에서 `models/*` 제외 규칙을 Space 저장소에서는 지워야 합니다)

⚠️ 무료 Space 의 디스크는 **재시작 시 초기화**됩니다. SQLite 기록과 `static/results` 이미지가 사라지므로,
분석 기록을 유지하려면 외부 PostgreSQL 을 `DATABASE_URL` 로 연결하세요.

로컬 Docker 테스트:
```bash
docker build -t authenticity-backend .
docker run -p 7860:7860 authenticity-backend
# → http://localhost:7860/health
```
