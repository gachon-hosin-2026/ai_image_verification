// 백엔드 서버와 통신하는 코드
// 1. 서버 주소는 .env.local 의 NEXT_PUBLIC_API_BASE 로 정함 (없으면 http://localhost:8000)
//    그래서 터널 주소·HF Spaces 주소로 바뀌어도 코드 수정 없이 .env.local 한 줄만 바꾸면 됨
// 2. 서버가 보낸 한국어 오류 메시지(detail)를 그대로 Error 로 던짐. 화면은 그 메시지를 보여주기만 하면 됨
// 3. 저장된 접근 키를 모든 요청에 X-Access-Key 헤더로 붙임. 401 이면 AuthError 로 구분해서 던짐
import { accessKey } from "./accessKey";
import type { AnalysisResult, Health, RecompressResult, UserLabel } from "./types";

export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000").replace(/\/$/, "");

// 백엔드가 주는 /static/... 상대 경로를 전체 주소로 바꿈
export function assetUrl(path: string): string {
  return path.startsWith("http") ? path : `${API_BASE}${path}`;
}

// 접근 키 문제(401)를 다른 오류와 구분하기 위한 오류 종류
export class AuthError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  const key = accessKey.get();
  if (key) headers.set("X-Access-Key", key);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch {
    throw new Error("서버에 연결할 수 없습니다. 백엔드 서버가 켜져 있는지 확인하세요.");
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = body && typeof body.detail === "string" ? body.detail : `요청 실패 (HTTP ${res.status})`;
    if (res.status === 401) throw new AuthError(detail);
    throw new Error(detail);
  }
  return body as T;
}

const json = (data: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(data),
});

export function getHealth() {
  return request<Health>("/health");
}

export function analyzeImage(file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<AnalysisResult>("/api/v1/analyze/image", { method: "POST", body: form });
}

export function analyzeUrl(url: string) {
  return request<AnalysisResult>("/api/v1/analyze/url", json({ url }));
}

export function recompressTest(analysisId: string) {
  return request<RecompressResult>("/api/v1/analyze/recompress-test", json({ analysis_id: analysisId }));
}

export function sendFeedback(analysisId: string, label: UserLabel, comment?: string) {
  return request<{ feedback_id: number }>("/api/v1/feedback", json({ analysis_id: analysisId, user_label: label, comment }));
}
