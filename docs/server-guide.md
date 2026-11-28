# 공용 서버 운영 안내 (관리자용)

공용 서버는 **팀원·교수님이 접속하는 실제 운영 사이트**이자 **학습 데이터가 쌓이는 곳**입니다.
항상 main 에 병합된 코드만 실행합니다.

```
인터넷 → Tailscale Funnel (https://xodus217.taile57f46.ts.net)
           → 프론트 (127.0.0.1:3000, Next.js 운영 빌드)
                → /api, /docs, /static 은 백엔드로 전달 (127.0.0.1:8000, FastAPI)
```
프론트·백엔드 모두 `127.0.0.1` 로만 열려 있어서, 외부에서는 Funnel 을 통해서만 들어올 수 있습니다.

---

## 1. 처음 한 번만: 공용 서버 폴더 만들기

개발용 폴더(`C:\Dev\p-project`)와 **반드시 다른 폴더**를 씁니다.
개발 중인 코드가 팀 서버에 섞이지 않게 하기 위함입니다.

```cmd
cd C:\Dev
git clone https://github.com/gachon-hosin-2026/ai_image_verification.git p-project-server
copy C:\Dev\p-project-server\backend\.env.example C:\Dev\p-project-server\backend\.env
```

`C:\Dev\p-project-server\backend\.env` 를 열어 **접근 키**를 넣습니다.
```
ACCESS_KEY=여기에_키
```
키 만들기 (아무 터미널에서):
```cmd
python -c "import secrets; print(secrets.token_urlsafe(24))"
```
- `=` 앞뒤에 공백·따옴표 없이, 같은 줄에 붙여넣기
- 키는 **팀원에게 개인 메시지로만** 공유 (저장소가 Public 이라 README·이슈에 쓰면 안 됨)

Tailscale 이 설치·로그인돼 있어야 합니다. (`winget install --id Tailscale.Tailscale`)

---

## 2. 매일 쓰는 것

모두 `C:\Dev\p-project-server\scripts\` 에 있습니다. **더블클릭**하면 됩니다.

| 상황 | 실행 | 결과 |
|---|---|---|
| 서버 켜기 | `start-server.bat` | `SERVER-backend`, `SERVER-frontend`, `SERVER-funnel` 창 3개가 열림 |
| PR 이 main 에 병합됨 | `update-server.bat` | 서버 끄기 → `git pull` → 패키지·빌드 → 다시 켜기 |
| 테스트 끝 / 외출 / 취침 | `stop-server.bat` | 서버 끄기 + 외부 공개 닫기 |

- 처음 실행 때는 패키지 설치·빌드로 몇 분 걸립니다. 다음부터는 바로 켜집니다.
- `start-server` 는 **main 브랜치가 아니거나 접근 키가 비어 있으면 실행을 거부**합니다. (실수 방지)
- 공용 서버 폴더에서는 **코드를 직접 고치지 마세요.** 고치면 `update-server` 의 `git pull` 이 실패합니다.

### 확인
- 휴대폰(와이파이 끄고 LTE)으로 공용 주소 접속 → 웹사이트가 보이면 정상
- 사이드바 아래 **서버 연결됨** 초록불 + 접근 키 입력 후 분석되면 정상

---

## 3. 접근 키 관리

| 상황 | 할 일 |
|---|---|
| 새 팀원 | 키를 개인 메시지로 전달 → 사이드바 **접근 키** 칸에 입력 |
| 키 유출 의심 | 새 키 만들기 → `.env` 수정 → `stop-server` → `start-server` (옛 키 즉시 무효) → 팀원에게 새 키 전달 |
| 로그에 모르는 IP 의 `200 OK` 분석 요청이 계속 보임 | 키 유출 신호 → 위와 같이 교체 |

로그에 `/.env`, `/wp-config.php` 같은 요청이 `404` 로 찍히는 건 인터넷 전체를 도는 자동 봇입니다. 정상적으로 막히고 있는 것이니 신경 쓰지 않아도 됩니다.

---

## 4. 학습 데이터

공용 서버에서 분석한 기록은 `backend\app.db`, 이미지는 `backend\app\static\results\` 에 쌓입니다.
- 업로드 시 **"학습 데이터 활용 동의"** 를 체크한 기록만 `train_consent = 1` 로 저장됩니다.
- URL 분석은 원본 주소(`source_url`)가 함께 저장되어, 공인된 출처의 이미지만 골라낼 수 있습니다.
- 이 파일들은 Git 에 올라가지 않습니다. **지우지 마세요.**

> TODO: 학습 데이터 내보내기 + Hugging Face Dataset(비공개) 자동 백업 — 다음 PR 에서 추가 예정

---

## 5. 문제 해결

| 증상 | 원인 / 해결 |
|---|---|
| "포트 8000(3000)이 이미 사용 중" | 서버가 이미 켜져 있음 → `update-server` 또는 `stop-server` 후 `start-server` |
| "main 브랜치에서만 실행합니다" | 개발 폴더에서 실행한 것 → 공용 서버 폴더(`p-project-server`)에서 실행 |
| "ACCESS_KEY 가 비어 있습니다" | 다른 폴더의 `.env` 를 고쳤을 가능성 → `p-project-server\backend\.env` 확인 |
| 공용 주소가 안 열림 | `SERVER-funnel` 창이 닫혔거나 PC 가 절전 → `start-server` 다시 실행, 절전 끄기 |
| 웹사이트는 열리는데 분석이 안 됨 | `SERVER-backend` 창 오류 확인 / 사이드바 접근 키 확인 |
| `git pull` 실패 | 공용 서버 폴더에서 파일을 고친 경우 → `git status` 로 확인 후 `git restore .` |
