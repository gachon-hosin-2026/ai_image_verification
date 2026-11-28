// 최근 분석 기록을 브라우저(localStorage)에 저장하는 코드
// 1. 최대 30건까지 최신순으로 보관. 그래서 새로고침해도 '분석 기록' 화면에 남아 있음
// 2. 브라우저마다 따로 저장됨 (팀원끼리 공유 안 됨)
// TODO: 백엔드에 GET /api/v1/analyses 목록 API 가 생기면 이 파일 대신 서버 기록을 불러오도록 교체
import type { AnalysisResult } from "./types";

export interface HistoryItem {
  result: AnalysisResult;
  source: string; // 파일 이름 또는 URL
  at: number;
}

const KEY = "jinwi-history-v1";
const MAX = 30;
const EMPTY: HistoryItem[] = [];
let cache: HistoryItem[] | null = null;
const listeners = new Set<() => void>();

function read(): HistoryItem[] {
  if (cache) return cache;
  try {
    cache = JSON.parse(localStorage.getItem(KEY) ?? "[]");
  } catch {
    cache = [];
  }
  return cache ?? EMPTY;
}

function write(items: HistoryItem[]) {
  cache = items;
  try {
    localStorage.setItem(KEY, JSON.stringify(items));
  } catch {
    /* 저장 공간 부족·시크릿 모드 등은 무시 (메모리에는 남음) */
  }
  listeners.forEach((fn) => fn());
}

export const history = {
  subscribe(fn: () => void) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  },
  getSnapshot: read,
  getServerSnapshot: () => EMPTY,
  add(result: AnalysisResult, source: string) {
    const rest = read().filter((h) => h.result.analysis_id !== result.analysis_id);
    write([{ result, source, at: Date.now() }, ...rest].slice(0, MAX));
  },
  clear() {
    write([]);
  },
};
