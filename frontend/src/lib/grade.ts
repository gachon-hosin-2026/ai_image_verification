// 등급·조작 범위를 화면용 한국어 이름과 색으로 바꾸는 코드
// 1. 백엔드는 영어 Enum 만 보내므로, 사용자에게 보이는 글자는 전부 여기서 정함
import type { Grade, Scope } from "./types";

export const GRADE_INFO: Record<Grade, { label: string; short: string; color: string; range: string }> = {
  SAFE_LIKELY_REAL: { label: "실사 유력", short: "안전", color: "var(--color-safe)", range: "80–100" },
  CAUTION_EDITED_OR_RECOMPRESSED: { label: "편집·재압축 의심", short: "주의", color: "var(--color-caution)", range: "55–79" },
  WARNING_AI_SUSPECTED: { label: "AI 생성 의심", short: "경고", color: "var(--color-warning)", range: "30–54" },
  DANGER_HIGHLY_LIKELY_AI: { label: "AI 생성 매우 유력", short: "위험", color: "var(--color-danger)", range: "0–29" },
};

export const SCOPE_INFO: Record<Scope, { label: string; desc: string }> = {
  LIKELY_AUTHENTIC: { label: "실사 유력", desc: "조작 흔적이 뚜렷하지 않습니다." },
  LOCAL_EDIT_SUSPECTED: { label: "부분 보정·합성 의심", desc: "이미지 일부 영역에서만 이상 신호가 모여 있습니다." },
  GLOBAL_AI_GENERATED: { label: "AI 전면 생성 의심", desc: "이미지 전체에 생성형 AI 특유의 패턴이 퍼져 있습니다." },
};
