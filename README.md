# ai_image_verification — AI 이미지 진위 판별

업로드한 이미지나 뉴스·커뮤니티 URL 의 이미지가 **실제 촬영인지 AI 생성인지** 0–100점과 근거로 보여주는 팩트체크 서비스입니다.
점수가 **높을수록 실제 촬영**, 낮을수록 AI 생성입니다.

## 저장소 구조

```
ai_image_verification/
├── backend/            # FastAPI 서버 + 분석 엔진 (Python)
│   ├── app/api/        #   API 주소 처리          ← 백엔드 담당
│   ├── app/core/       #   설정·보안              ← 백엔드 담당
│   ├── app/pipeline/   #   Stage 0~5 분석 엔진     ← AI·포렌식 담당 (stage1~5 채우기)
│   └── README.md       #   실행·외부 공개·배포 방법
├── frontend/           # Next.js 웹 화면 (TypeScript)   ← 프론트 담당
│   └── README.md       #   실행 방법·파일 구조
└── .github/            # 이슈·PR 템플릿, 자동 검사
```

각 폴더의 README 에 실행 방법이 있습니다.
- 백엔드: [backend/README.md](backend/README.md)
- 프론트: [frontend/README.md](frontend/README.md)

## 작업 흐름 (팀 규칙)

**이슈 → 브랜치 → 커밋 → PR → 리뷰 → 병합 → 정리**
main 에 직접 push 하지 않습니다. 누가 언제 무엇을 했는지 기록을 남기기 위함입니다.

### 1. 이슈 만들기
GitHub 의 **Issues → New issue** 에서 템플릿(기능 / 버그)을 골라 할 일을 적습니다. 이슈 번호(예: `#12`)를 기억해 두세요.

### 2. 최신 main 받고 브랜치 만들기
```bash
git switch main
git pull
git switch -c feat/backend-access-key
```

### 3. 작게 자주 커밋
```bash
git add backend/app/core/security.py
git commit -m "feat: 접근 키 검사 추가 (#12)"
```
- `git add .` 대신 **파일을 골라서** add 하면 실수로 남의 파일이나 비밀 파일을 올리는 일을 막을 수 있습니다.

### 4. push 하고 PR 만들기
```bash
git push -u origin feat/backend-access-key
```
GitHub 에 뜨는 **Compare & pull request** 버튼 → 템플릿 칸을 채우고 본문에 `Closes #12` 를 적습니다.

### 5. 리뷰·승인
다른 팀원 1명 이상이 **Files changed** 탭에서 코드를 보고 **Approve** 합니다. 자동 검사(Actions)가 초록불인지도 확인합니다.

### 6. 병합 후 브랜치 삭제
**Squash and merge** → **Delete branch**. 이슈는 `Closes #12` 덕분에 자동으로 닫힙니다.

### 7. 내 컴퓨터 main 최신화
```bash
git switch main
git pull
git branch -d feat/backend-access-key
```

## 이름 규칙

| 종류 | 형식 | 예시 |
|---|---|---|
| 브랜치 | `종류/영역-내용` | `feat/backend-access-key`, `fix/frontend-upload-error`, `docs/readme-update` |
| 커밋 | `종류: 한 일 (#이슈)` | `feat: 재압축 테스트 카드 추가 (#7)` |

종류: `feat`(기능) · `fix`(버그) · `docs`(문서) · `refactor`(구조 정리) · `test`(테스트) · `chore`(설정·기타)
영역: `backend` · `frontend` · `pipeline` · `infra`

## 꼭 지킬 것

- **비밀 정보 금지**: 이 저장소는 Public 입니다. 접근 키·비밀번호는 `.env` 에만 넣고 절대 커밋하지 마세요.
- **큰 파일 금지**: 모델 가중치(`.onnx`, `.joblib`), 학습 이미지, DB 파일은 올리지 않습니다. (`.gitignore` 로 막혀 있음)
- **API 형식 변경 시**: `backend/app/schemas/analysis.py` 를 바꾸면 `frontend/src/lib/types.ts` 도 **같은 PR 에서** 함께 고치세요.
- **주석 스타일**: 파일·함수 위에 `무엇을 하는 코드` 한 줄 + `1. 어떻게 진행 → 어디에 영향` 번호 목록.
