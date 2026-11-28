# 진위판별 — 프론트엔드 (Next.js)

AI 이미지 진위 판별 서비스의 웹 화면입니다. 디자인은 [designbookmark.com/motion](https://designbookmark.com/motion) 의 다크 톤을 참고했습니다.

## 실행 방법

**가장 쉬운 방법:** 저장소 루트의 `scripts\start-dev.bat` 더블클릭 → 백엔드·프론트가 같이 켜지고 http://localhost:3001 이 열립니다.

직접 실행하려면 (Node.js 22 권장, 최소 20.9):
```cmd
cd frontend
npm install
npm run dev
```
→ http://localhost:3000. 이 경우 **백엔드가 127.0.0.1:8000 에 켜져 있어야** 분석이 됩니다.

### 백엔드와 연결되는 방식 (프록시)
브라우저는 항상 **같은 주소**(`/api/...`)로 요청하고, Next 서버가 `next.config.ts` 의 프록시로 백엔드에 전달합니다.
그래서 주소가 하나로 통일되고 CORS 설정이 필요 없습니다. 사이드바에는 `같은 주소 (프록시)` 로 표시됩니다.

## 접근 키

백엔드에 `ACCESS_KEY` 가 설정돼 있으면, 사이드바 아래 **접근 키** 칸에 팀에서 받은 키를 한 번 입력하세요.
- 키는 이 브라우저에만 저장됩니다. 다른 브라우저·기기에서는 다시 입력해야 합니다.
- 키가 틀리면 분석할 때 오류 아래에 입력칸이 다시 나타납니다.
- ⚠️ 키를 코드나 `.env.local` 에 넣지 마세요. 프론트 코드는 누구나 볼 수 있어서 키가 공개됩니다.

## 백엔드 주소 바꾸기

기본은 같은 PC 의 백엔드(`http://127.0.0.1:8000`)입니다. 다른 백엔드에 붙이려면 `frontend\.env.local` 에 한 줄 넣고 다시 실행하세요.
```
BACKEND_URL=https://xodus217.taile57f46.ts.net    # 공용 서버에 붙이기 (프론트만 개발할 때)
```
- `start-dev.bat -UsePublicServer` 를 쓰면 이 설정 없이 자동으로 공용 서버에 붙습니다.
- `npm run build` 할 때의 값이 빌드 결과에 고정되므로, 바꾼 뒤에는 다시 빌드하세요.
- 업로드는 프록시를 거쳐도 최대 20MB 까지 됩니다 (`next.config.ts` 의 `proxyClientMaxBodySize`).

## 파일 구조 (어디를 고치면 되는지)

| 파일 | 하는 일 |
|---|---|
| `src/app/globals.css` | 색·모양 디자인 토큰. **전체 색을 바꾸려면 여기만** |
| `src/app/layout.tsx` | 폰트(Pretendard, Geist Mono), 페이지 제목 |
| `next.config.ts` | 백엔드 프록시 주소·업로드 한도 |
| `src/components/Home.tsx` | 메인 화면. 분석 흐름, 결과 카드 배치, 학습 데이터 동의 체크박스 |
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

## 운영 배포

지금은 공용 서버(태연 PC)에서 `scripts\start-server.bat` 로 운영 빌드를 실행합니다. 자세한 내용은 [docs/server-guide.md](../docs/server-guide.md).
> Vercel 은 조직 저장소를 무료 플랜으로 바로 연결할 수 없어 보류 중입니다 (회의 안건).
