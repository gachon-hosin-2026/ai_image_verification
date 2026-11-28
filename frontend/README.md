# 진위판별 — 프론트엔드 (Next.js)

AI 이미지 진위 판별 서비스의 웹 화면입니다. 디자인은 [designbookmark.com/motion](https://designbookmark.com/motion) 의 다크 톤을 참고했습니다.

## 실행 방법

> Node.js 22 이상 권장 (최소 20.9) (`node -v` 로 확인)

```cmd
cd C:\Dev\p-project\frontend
npm install
npm run dev
```

브라우저에서 http://localhost:3000 접속. **백엔드 서버(localhost:8000)가 켜져 있어야** 분석이 됩니다.
사이드바 아래 '서버 연결됨' 초록불로 연결 상태를 확인할 수 있습니다.

## 접근 키

백엔드에 `ACCESS_KEY` 가 설정돼 있으면, 사이드바 아래 **접근 키** 칸에 팀에서 받은 키를 한 번 입력하세요.
- 키는 이 브라우저에만 저장됩니다. 다른 브라우저·기기에서는 다시 입력해야 합니다.
- 키가 틀리면 분석할 때 오류 아래에 입력칸이 다시 나타납니다.
- ⚠️ 키를 코드나 `.env.local` 에 넣지 마세요. 프론트 코드는 누구나 볼 수 있어서 키가 공개됩니다.

## 백엔드 주소 바꾸기

기본값은 `http://localhost:8000` 이라 로컬에서는 설정 없이 동작합니다.
주소를 바꾸려면 `frontend` 폴더에 `.env.local` 파일을 만들고 아래 한 줄을 넣은 뒤 `npm run dev` 를 다시 실행하세요.

```
NEXT_PUBLIC_API_BASE=http://localhost:8000              # 로컬
NEXT_PUBLIC_API_BASE=https://pc이름.tailXXXX.ts.net     # Tailscale Funnel 고정 주소
NEXT_PUBLIC_API_BASE=https://아이디-스페이스.hf.space     # HF Spaces 배포 후
```

## 파일 구조 (어디를 고치면 되는지)

| 파일 | 하는 일 |
|---|---|
| `src/app/globals.css` | 색·모양 디자인 토큰. **전체 색을 바꾸려면 여기만** |
| `src/app/layout.tsx` | 폰트(Pretendard, Geist Mono), 페이지 제목 |
| `src/components/Home.tsx` | 메인 화면. 분석 흐름과 결과 카드 배치 |
| `src/components/Sidebar.tsx` | 왼쪽 메뉴, 등급 범례, 서버 상태 |
| `src/components/UploadStage.tsx` | 이미지 드래그&드롭 업로드 |
| `src/components/UrlBar.tsx` | 하단 URL 입력창 |
| `src/components/result/*.tsx` | 결과 카드 6종 (점수, 시각 증거, 점수 근거, 세부 지표, 재압축 테스트, 피드백) |
| `src/components/HistoryView.tsx` | 분석 기록 화면 |
| `src/components/GuideView.tsx` | 점수 읽는 법 화면 |
| `src/components/ui.tsx` | 카드·칩·버튼 공통 부품 |
| `src/lib/api.ts` | 백엔드 API 호출 |
| `src/lib/types.ts` | API 응답 타입 (백엔드 스키마와 1:1) |
| `src/lib/grade.ts` | 등급·조작 범위의 한국어 이름과 색 |
| `src/lib/history.ts` | 분석 기록 (브라우저 localStorage) |

이어서 할 일은 코드 안의 `TODO` 주석으로 표시해 두었습니다. (VS Code 검색: `TODO`)

## Vercel 배포 (Week 3~)

1. GitHub 에 push → https://vercel.com 에서 저장소 Import
2. Root Directory 를 `frontend` 로 지정
3. Environment Variables 에 `NEXT_PUBLIC_API_BASE` = HF Spaces 백엔드 주소 입력
4. 백엔드 `.env` 의 `ALLOW_ORIGINS` 에 Vercel 주소 추가
